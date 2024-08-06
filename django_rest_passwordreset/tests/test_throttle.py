from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django_rest_passwordreset.models import ResetPasswordToken


User = get_user_model()


class TestThrottle(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.user_1 = User.objects.create_user(username='user_1', password='password', email='user@test.local')
        self.user_admin = User.objects.create_superuser(username='admin', password='password', email='admin@test.local')

    def test_0001_login(self):

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

    def test_0002_throttle(self):

        # first run on test_0001_login
        # x number of runs (adjust number of calls to the throttle settings)
        for i in range(1):
            self.test_0001_login()

        # last run should raise an exception
        self.assertRaises(Exception, self.test_0001_login())
