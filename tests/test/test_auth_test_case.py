import json
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework.test import APITestCase
from django_rest_passwordreset.models import ResetPasswordToken
from tests.test.helpers import HelperMixin, patch


class AuthTestCase(APITestCase, HelperMixin):
    """
    Several Test Cases for the Multi Auth Token Django App
    """
    def setUp(self):
        self.setUpUrls()
        self.user1 = User.objects.create_user("user1", "user1@mail.com", "secret1")
        self.user2 = User.objects.create_user("user2", "user2@mail.com", "secret2")

    def test_try_reset_password_email_does_not_exist(self):
        """ Tests requesting a token for an email that does not exist """
        response = self.rest_do_request_reset_token(email="foobar@doesnotexist.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        decoded_response = json.loads(response.content.decode())
        # response should have "email" in it
        self.assertTrue("email" in decoded_response)

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
    def test_reset_password_multiple_users(self, mock_reset_password_token_created):
        """ Checks whether multiple password reset tokens can be created for different users """
        # connect signal
        # we need to check whether the signal is getting called


        # create a token for user 1
        response = self.rest_do_request_reset_token(email="user1@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)
        self.assertTrue(mock_reset_password_token_created.called)
        self.assertEquals(mock_reset_password_token_created.call_count, 1)
        token1 = mock_reset_password_token_created.call_args[1]['reset_password_token']

        # create another token for user 2
        response = self.rest_do_request_reset_token(email="user2@mail.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = ResetPasswordToken.objects.all()
        self.assertEqual(tokens.count(), 2)
        self.assertEquals(mock_reset_password_token_created.call_count, 2)
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
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

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
        self.assertEquals(mock_reset_password_token_created.call_count, 1)

        token1 = mock_reset_password_token_created.call_args[1]['reset_password_token']
        self.assertNotEqual(token1.key, "", msg="Verify that the reset_password_token of the reset_password_Token_created signal is not empty")

        # verify that the other two signals have not yet been called
        self.assertFalse(mock_post_password_reset.called)
        self.assertFalse(mock_pre_password_reset.called)

        # reset password
        response = self.rest_do_reset_password_with_token(token1.key, "new_secret")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # now the other two signals should have been called
        self.assertTrue(mock_post_password_reset.called)
        self.assertTrue(mock_pre_password_reset.called)
