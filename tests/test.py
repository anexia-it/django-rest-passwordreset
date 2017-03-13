import json
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework.test import APITestCase
from django_rest_multitokenauth.models import MultiToken, ResetPasswordToken

# try getting reverse from django.urls
try:
    # Django 1.10 +
    from django.urls import reverse
except:
    # Django 1.8 and 1.9
    from django.core.urlresolvers import reverse


reset_password_token_signal_call_count = 0
last_reset_password_token = ""

def count_reset_password_token_signal(reset_password_token, *args, **kwargs):
    global reset_password_token_signal_call_count, last_reset_password_token
    reset_password_token_signal_call_count += 1
    last_reset_password_token = reset_password_token


class HelperMixin:
    """
    Mixin which encapsulates methods for login, logout, request reset password and reset password confirm
    """
    def setUpUrls(self):
        """ set up urls by using djangos reverse function """
        self.reset_password_request_url = reverse('password_reset:auth-reset-password-request')
        self.reset_password_confirm_url = reverse('password_reset:auth-reset-password-confirm')

    def django_check_login(self, username, password):
        # ToDo: Check Login
        pass

    def rest_do_request_reset_token(self, email, HTTP_USER_AGENT='', REMOTE_ADDR='127.0.0.1'):
        """ REST API wrapper for requesting a password reset token """
        data = {
            'email': email
        }

        return self.client.post(
            self.reset_password_request_url,
            data,
            format='json',
            HTTP_USER_AGENT=HTTP_USER_AGENT,
            REMOTE_ADDR=REMOTE_ADDR
        )

    def rest_do_reset_password_with_token(self, token, new_password, HTTP_USER_AGENT='', REMOTE_ADDR='127.0.0.1'):
        """ REST API wrapper for requesting a password reset token """
        data = {
            'token': token,
            'password': new_password
        }

        return self.client.post(
            self.reset_password_confirm_url,
            data,
            format='json',
            HTTP_USER_AGENT=HTTP_USER_AGENT,
            REMOTE_ADDR=REMOTE_ADDR
        )


class AuthTestCase(APITestCase, HelperMixin):
    """
    Several Test Cases for the Multi Auth Token Django App
    """
    def setUp(self):
        self.setUpUrls()
        self.user1 = User.objects.create_user("user1", "user1@mail.com", "secret1")
        self.user2 = User.objects.create_user("user2", "user2@mail.com", "secret2")

    def test_reset_password(self):
        """ Tests resetting a password """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # we need to check whether the signal is getting called
        global reset_password_token_signal_call_count
        reset_password_token_signal_call_count = 0

        from django_rest_passwordreset.signals import reset_password_token_created
        reset_password_token_created.connect(count_reset_password_token_signal)

        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(reset_password_token_signal_call_count, 1)
        self.assertNotEqual(last_reset_password_token, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # if the same user tries to reset again, the user will get the same token again
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(reset_password_token_signal_call_count, 2)
        self.assertNotEqual(last_reset_password_token, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        # and it should be assigned to user1
        self.assertEqual(
            ResetPasswordToken.objects.filter(key=last_reset_password_token.key).first().user.username,
            "user1"
        )

        # try to reset the password
        response = self.rest_do_reset_password_with_token(last_reset_password_token.key, "new_secret")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # try to login with the old username/password (should fail)
        self.assertFalse(
            self.django_check_login("user1", "secret1"),
            msg="User 1 should not be able to login with the old credentials"
        )

        # try to login with the new username/Password (should work)
        self.assertTrue(
            self.django_check_login("user1", "new_secret"),
            msg="User 1 should be able to login with the modified credentials"
        )

    def test_reset_password_multiple_users(self):
        """ Checks whether multiple password reset tokens can be created for different users """
        # connect signal
        # we need to check whether the signal is getting called
        global reset_password_token_signal_call_count, last_reset_password_token
        reset_password_token_signal_call_count = 0

        from django_rest_passwordreset.signals import reset_password_token_created
        reset_password_token_created.connect(count_reset_password_token_signal)

        # create a token for user 1
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        token1 = last_reset_password_token

        # create another token for user 2
        response = self.rest_do_request_reset_token(email="user2@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = ResetPasswordToken.objects.all()
        self.assertEqual(tokens.count(), 2)
        token2 = last_reset_password_token

        # validate that those two tokens are different
        self.assertNotEqual(tokens[0].key, tokens[1].key)

        # try to request another token, there should still always be two keys
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResetPasswordToken.objects.all().count(), 2)

        # create another token for user 2
        response = self.rest_do_request_reset_token(email="user2@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResetPasswordToken.objects.all().count(), 2)

        # try to reset password of user2
        response = self.rest_do_reset_password_with_token(token2.key, "secret2_new")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # now there should only be one token left (token1)
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        self.assertEqual(ResetPasswordToken.objects.filter(key=token1.key).count(), 1)

        # user 2 should be able to login with "secret2_new" now
        self.assertTrue(
            self.django_check_login("user", "secret2_new"),
        )

        # try to reset again with token2 (should not work)
        response = self.rest_do_reset_password_with_token(token2.key, "secret2_fake_new")
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

        # user 2 should still be able to login with "secret2_new" now
        self.assertTrue(
            self.django_check_login("user2", "secret2_new"),
        )




