from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView

from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.throttling import (
    ResetPasswordRequestTokenThrottle,
    get_password_reset_request_token_throttle_classes,
)
from django_rest_passwordreset.views import ResetPasswordConfirm, ResetPasswordRequestToken, ResetPasswordValidateToken


User = get_user_model()


class TestThrottle(APITestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.user_1 = User.objects.create_user(username='user_1', password='password', email='user@test.local')
        self.user_admin = User.objects.create_superuser(username='admin', password='password', email='admin@test.local')

    def _reset_password_logged_in(self):
        # generate token
        url = reverse('password_reset:reset-password-request')
        data = {'email': self.user_1.email}
        response = self.client.post(url, data).json()

        self.assertIn('status', response)
        self.assertEqual(response['status'], 'OK')

        # test validity of the token
        token = ResetPasswordToken.objects.filter(user=self.user_1).first()
        url = reverse('password_reset:reset-password-validate')
        data = {'token': token.key}
        response = self.client.post(url, data).json()

        self.assertIn('status', response)
        self.assertEqual(response['status'], 'OK')

        # reset password
        url = reverse('password_reset:reset-password-confirm')
        data = {'token': token.key, 'password': 'new_password'}
        response = self.client.post(url, data).json()

        # check if new password was set
        self.assertTrue(token.user.check_password('new_password'))
        self.assertFalse(token.user.check_password('password'))

    def test_request_token_endpoint_keeps_library_throttle_default(self):
        throttles = ResetPasswordRequestToken().get_throttles()
        self.assertEqual(len(throttles), 1)
        self.assertIsInstance(throttles[0], ResetPasswordRequestTokenThrottle)

    def test_request_token_throttle_classes_default_to_library_throttle(self):
        self.assertEqual(
            get_password_reset_request_token_throttle_classes(),
            (ResetPasswordRequestTokenThrottle,),
        )

    @override_settings(
        DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES=["rest_framework.throttling.AnonRateThrottle"],
    )
    def test_request_token_throttle_classes_can_be_replaced(self):
        self.assertEqual(
            get_password_reset_request_token_throttle_classes(),
            (AnonRateThrottle,),
        )

    @override_settings(
        DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES=[],
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
            ],
        },
    )
    def test_empty_request_token_throttle_classes_delegate_to_drf_defaults(self):
        self.assertEqual(
            get_password_reset_request_token_throttle_classes(),
            (AnonRateThrottle,),
        )

    @override_settings(
        DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES=["rest_framework.throttling.ScopedRateThrottle"],
    )
    def test_request_token_endpoint_uses_configured_throttle_classes(self):
        self._assert_endpoint_uses_scoped_throttle(
            reverse('password_reset:reset-password-request'),
            {'email': self.user_1.email},
            ResetPasswordRequestToken.throttle_scope,
            '192.0.2.30',
        )

    @override_settings(
        DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES=[],
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.ScopedRateThrottle",
            ],
        },
    )
    def test_empty_request_token_throttle_classes_endpoint_uses_drf_defaults(self):
        self._assert_endpoint_uses_scoped_throttle(
            reverse('password_reset:reset-password-request'),
            {'email': self.user_1.email},
            ResetPasswordRequestToken.throttle_scope,
            '192.0.2.40',
        )

    @override_settings(
        DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES=[],
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.ScopedRateThrottle",
            ],
        },
    )
    def test_scoped_throttle_without_matching_rate_raises_improperly_configured(self):
        cache.clear()
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {}):
            with self.assertRaises(ImproperlyConfigured):
                self.client.post(
                    reverse('password_reset:reset-password-request'),
                    {'email': self.user_1.email},
                    format='json',
                    REMOTE_ADDR='192.0.2.50',
                )

    def test_validate_and_confirm_endpoints_do_not_override_global_throttle_classes(self):
        for view_class in (ResetPasswordValidateToken, ResetPasswordConfirm):
            self.assertNotIn("throttle_classes", view_class.__dict__)

    def test_password_reset_endpoints_expose_scoped_throttle_names(self):
        self.assertEqual(
            ResetPasswordRequestToken.throttle_scope,
            "django-rest-passwordreset-request-token",
        )
        self.assertEqual(
            ResetPasswordValidateToken.throttle_scope,
            "django-rest-passwordreset-validate-token",
        )
        self.assertEqual(
            ResetPasswordConfirm.throttle_scope,
            "django-rest-passwordreset-confirm",
        )

    def _assert_endpoint_uses_scoped_throttle(self, url, data, scope, remote_addr):
        cache.clear()
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {scope: "1/day"}):
            response = self.client.post(url, data, format='json', REMOTE_ADDR=remote_addr)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response = self.client.post(url, data, format='json', REMOTE_ADDR=remote_addr)
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_validate_endpoint_uses_inherited_scoped_throttle(self):
        token = ResetPasswordToken.objects.create(user=self.user_1)
        with mock.patch.object(APIView, "throttle_classes", (ScopedRateThrottle,)):
            self._assert_endpoint_uses_scoped_throttle(
                reverse('password_reset:reset-password-validate'),
                {'token': token.key},
                ResetPasswordValidateToken.throttle_scope,
                '192.0.2.10',
            )

    def test_confirm_endpoint_uses_inherited_scoped_throttle(self):
        token = ResetPasswordToken.objects.create(user=self.user_1)
        with mock.patch.object(APIView, "throttle_classes", (ScopedRateThrottle,)):
            self._assert_endpoint_uses_scoped_throttle(
                reverse('password_reset:reset-password-confirm'),
                {'token': token.key, 'password': 'new_password'},
                ResetPasswordConfirm.throttle_scope,
                '192.0.2.20',
            )

    @mock.patch(
        "django_rest_passwordreset.throttling.ResetPasswordRequestTokenThrottle.scope",
        "django-rest-passwordreset-request-token-test-scope",
    )
    def test_throttle(self,):
        # first run on _reset_password_logged_in
        # x number of runs (adjust number of calls to the throttle rate)
        for _ in range(1):
            self._reset_password_logged_in()
        # last run should raise an exception
        self.assertRaises(Exception, self._reset_password_logged_in)

    @mock.patch(
        "django_rest_passwordreset.throttling.ResetPasswordRequestTokenThrottle.scope",
        "django-rest-passwordreset-request-token-does-not-exist",
    )
    def test_throttle_default_rate(self):
        # first run on _reset_password_logged_in
        # x number of runs (adjust number of calls to the throttle rate)
        for _ in range(3):
            self._reset_password_logged_in()
        # last run should raise an exception
        self.assertRaises(Exception, self._reset_password_logged_in)
