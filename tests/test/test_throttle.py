from unittest import mock

from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from django_rest_passwordreset.models import ResetPasswordToken


User = get_user_model()


class TestThrottle(APITestCase):
    def setUp(self):
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
