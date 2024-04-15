import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from django_rest_passwordreset.models import ResetPasswordToken, get_password_reset_token_expiry_time
from django_rest_passwordreset.views import clear_expired_tokens, generate_token_for_email
from tests.test.helpers import HelperMixin, patch


class AuthTestCase(APITestCase, HelperMixin):
    """
    Several Test Cases for the Multi Auth Token Django App
    """

    def setUp(self):
        self.setUpUrls()
        self.user1 = User.objects.create_user("user1", "user1@mail.com", "secret1")
        self.user2 = User.objects.create_user("user2", "user2@mail.com", "secret2")
        self.user3 = User.objects.create_user("user3@mail.com", "not-that-mail@mail.com", "secret3")
        self.user4 = User.objects.create_user("user4", "user4@mail.com")
        self.user5 = User.objects.create_user("user5", "uѕer5@mail.com", "secret5")  # email contains kyrillic s

    def test_try_reset_password_email_does_not_exist(self):
        """ Tests requesting a token for an email that does not exist """
        response = self.rest_do_request_reset_token(email="foobar@doesnotexist.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        decoded_response = json.loads(response.content.decode())
        # response should have "email" in it
        self.assertTrue("email" in decoded_response)

    def test_unicode_email_reset(self):
        response = self.rest_do_request_reset_token(email="uѕer5@mail.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        decoded_response = json.loads(response.content.decode())
        self.assertEqual(decoded_response.get("email")[0], 'Enter a valid email address.')

    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    def test_validate_token(self, mock_reset_password_token_created):
        """ Tests validate token """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check that the signal was sent once
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEqual(mock_reset_password_token_created.call_count, 1)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        # and it should be assigned to user1
        self.assertEqual(
            ResetPasswordToken.objects.filter(key=last_reset_password_token.key).first().user.username,
            "user1"
        )

        # try to validate token
        response = self.rest_do_validate_token(last_reset_password_token.key)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # there should be no user details in the response
        self.assertEqual(response.data.get("username"), None)
        self.assertEqual(response.data.get("email"), None)

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # try to log in with the old username/password (should work)
        self.assertTrue(
            self.django_check_login("user1", "secret1"),
            msg="User 1 should still be able to login with the old credentials"
        )

    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    @override_settings(DJANGO_REST_PASSWORDRESET_USER_DETAILS_ON_VALIDATION=True)
    def test_validate_token_with_user_details(self, mock_reset_password_token_created):
        """ Tests validate token with user details in the response """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # try to validate token
        response = self.rest_do_validate_token(last_reset_password_token.key)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # there should be user details in the response
        self.assertEqual(response.data.get("username"), "user1")
        self.assertEqual(response.data.get("email"), "user1@mail.com")

    def test_validate_bad_token(self):
        """ Tests validate an invalid token """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # try to validate an invalid token
        response = self.rest_do_validate_token("not_a_valid_token")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    @override_settings(DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME=-1)
    def test_validate_expired_token(self, mock_reset_password_token_created):
        """ Tests validate an expired token """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check that the signal was sent once
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEqual(mock_reset_password_token_created.call_count, 1)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        # and it should be assigned to user1
        self.assertEqual(
            ResetPasswordToken.objects.filter(key=last_reset_password_token.key).first().user.username,
            "user1"
        )

        # try to validate token
        response = self.rest_do_validate_token(last_reset_password_token.key)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # try to login with the old username/password (should work)
        self.assertTrue(
            self.django_check_login("user1", "secret1"),
            msg="User 1 should still be able to login with the old credentials"
        )

    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    def test_reset_password(self, mock_reset_password_token_created):
        """ Tests resetting a password """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check that the signal was sent once
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEqual(mock_reset_password_token_created.call_count, 1)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # if the same user tries to reset again, the user will get the same token again
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_reset_password_token_created.call_count, 2)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

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

    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    @override_settings(DJANGO_REST_LOOKUP_FIELD='username')
    def test_reset_password_different_lookup(self, mock_reset_password_token_created):
        """ Tests resetting a password """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        response = self.rest_do_request_reset_token(email="user3@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check that the signal was sent once
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEqual(mock_reset_password_token_created.call_count, 1)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # if the same user tries to reset again, the user will get the same token again
        response = self.rest_do_request_reset_token(email="user3@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_reset_password_token_created.call_count, 2)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        # and it should be assigned to user1
        self.assertEqual(
            ResetPasswordToken.objects.filter(key=last_reset_password_token.key).first().user.username,
            "user3@mail.com"
        )

        # try to reset the password
        response = self.rest_do_reset_password_with_token(last_reset_password_token.key, "new_secret")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # try to login with the old username/password (should fail)
        self.assertFalse(
            self.django_check_login("user3@mail.com", "secret3"),
            msg="User 3 should not be able to login with the old credentials"
        )

        # try to login with the new username/Password (should work)
        self.assertTrue(
            self.django_check_login("user3@mail.com", "new_secret"),
            msg="User 3 should be able to login with the modified credentials"
        )

    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    def test_reset_password_multiple_users(self, mock_reset_password_token_created):
        """ Checks whether multiple password reset tokens can be created for different users """
        # connect signal
        # we need to check whether the signal is getting called

        # create a token for user 1
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEqual(mock_reset_password_token_created.call_count, 1)
        token1 = mock_reset_password_token_created.call_args[1]['reset_password_token']

        # create another token for user 2
        response = self.rest_do_request_reset_token(email="user2@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = ResetPasswordToken.objects.all()
        self.assertEqual(tokens.count(), 2)
        self.assertEqual(mock_reset_password_token_created.call_count, 2)
        token2 = mock_reset_password_token_created.call_args[1]['reset_password_token']

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
            self.django_check_login("user2", "secret2_new"),
        )

        # try to reset again with token2 (should not work)
        response = self.rest_do_reset_password_with_token(token2.key, "secret2_fake_new")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # user 2 should still be able to login with "secret2_new" now
        self.assertTrue(
            self.django_check_login("user2", "secret2_new"),
        )

    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    @patch('django_rest_passwordreset.signals.pre_password_reset.send')
    @patch('django_rest_passwordreset.signals.post_password_reset.send')
    def test_signals(self,
                     mock_post_password_reset,
                     mock_pre_password_reset,
                     mock_reset_password_token_created
                     ):
        # check that all mocks have not been called yet
        self.assertFalse(mock_reset_password_token_created.called)
        self.assertFalse(mock_post_password_reset.called)
        self.assertFalse(mock_pre_password_reset.called)

        # request token for user1
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # verify that the reset_password_token_created signal was fired
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEqual(mock_reset_password_token_created.call_count, 1)

        token1 = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(token1.key, "",
                            msg="Verify that the reset_password_token of the reset_password_Token_created signal is not empty")

        # verify that the other two signals have not yet been called
        self.assertFalse(mock_post_password_reset.called)
        self.assertFalse(mock_pre_password_reset.called)

        # reset password
        response = self.rest_do_reset_password_with_token(token1.key, "new_secret")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # now the other two signals should have been called
        self.assertTrue(mock_post_password_reset.called)
        self.assertIn('reset_password_token', mock_post_password_reset.call_args[1])
        self.assertEqual(mock_post_password_reset.call_args[1]['reset_password_token'], token1)
        self.assertTrue(mock_pre_password_reset.called)
        self.assertIn('reset_password_token', mock_pre_password_reset.call_args[1])
        self.assertEqual(mock_pre_password_reset.call_args[1]['reset_password_token'], token1)

    @override_settings(DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE=True)
    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    def test_try_reset_password_email_does_not_exist_no_leakage_enabled(self, mock_reset_signal):
        """
        Tests requesting a token for an email that does not exist when
        DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE == True
        """
        response = self.rest_do_request_reset_token(email="foobar@doesnotexist.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(mock_reset_signal.called)

    def test_user_without_password(self):
        """ Tests requesting a token for an email without a password doesn't work"""
        response = self.rest_do_request_reset_token(email="user4@mail.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        decoded_response = json.loads(response.content.decode())
        # response should have "email" in it
        self.assertTrue("email" in decoded_response)

    @override_settings(DJANGO_REST_MULTITOKENAUTH_REQUIRE_USABLE_PASSWORD=False)
    @patch('django_rest_passwordreset.signals.reset_password_token_created.send')
    def test_user_without_password_where_not_required(self, mock_reset_password_token_created):
        """ Tests requesting a token for an email without a password works when not required"""
        response = self.rest_do_request_reset_token(email="user4@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check that the signal was sent once
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEqual(mock_reset_password_token_created.call_count, 1)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # if the same user tries to reset again, the user will get the same token again
        response = self.rest_do_request_reset_token(email="user4@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_reset_password_token_created.call_count, 2)
        last_reset_password_token = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(last_reset_password_token.key, "")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        # and it should be assigned to user1
        self.assertEqual(
            ResetPasswordToken.objects.filter(key=last_reset_password_token.key).first().user.username,
            "user4"
        )

        # try to reset the password
        response = self.rest_do_reset_password_with_token(last_reset_password_token.key, "new_secret")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # try to login with the new username/Password (should work)
        self.assertTrue(
            self.django_check_login("user4", "new_secret"),
            msg="User 4 should be able to login with the modified credentials"
        )

    def test_clear_expired_tokens(self):
        """ Tests clearance of expired tokens """

        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # request a new token
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # let the token expire
        token = ResetPasswordToken.objects.all().first()
        token.created_at = timezone.now() - timedelta(hours=password_reset_token_validation_time)
        token.save()

        # clear expired tokens
        clear_expired_tokens()

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    def test_generate_token_for_email(self):
        """ Tests generating tokens for a specific email address programmatically """

        # there should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

        # request a new token
        generate_token_for_email(email="user1@mail.com")

        # there should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
