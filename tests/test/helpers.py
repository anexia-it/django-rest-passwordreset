from django.contrib.auth.models import User

try:
    from unittest.mock import patch
except:
    # Python 2.7 fallback
    from mock import patch

# try getting reverse from django.urls
try:
    # Django 1.10 +
    from django.urls import reverse
except:
    # Django 1.8 and 1.9
    from django.core.urlresolvers import reverse


__all__ = [
    "HelperMixin",
    "patch"
]


class HelperMixin:
    """
    Mixin which encapsulates methods for login, logout, request reset password and reset password confirm
    """
    def setUpUrls(self):
        """ set up urls by using djangos reverse function """
        self.reset_password_request_url = reverse('password_reset:reset-password-request')
        self.reset_password_confirm_url = reverse('password_reset:reset-password-confirm')
        self.reset_password_validate_token_url = reverse('password_reset:reset-password-validate')

    def django_check_login(self, username, password):
        """
        Checks the django login by querying the user from the database and calling check_password()
        :param username:
        :param password:
        :return:
        """
        user = User.objects.filter(username=username).first()

        return user.check_password(password)

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
        """ REST API wrapper for resetting a user's password using a token """
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

    def rest_do_validate_token(self, token, HTTP_USER_AGENT='', REMOTE_ADDR='127.0.0.1'):
        """ REST API wrapper for validating a token """
        data = {
            'token': token
        }

        return self.client.post(
            self.reset_password_validate_token_url,
            data,
            format='json',
            HTTP_USER_AGENT=HTTP_USER_AGENT,
            REMOTE_ADDR=REMOTE_ADDR
        )
