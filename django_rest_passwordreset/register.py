from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings
from rest_framework import status, serializers, exceptions
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django_rest_passwordreset.serializers import EmailSerializer, PasswordTokenSerializer, TokenSerializer
from django_rest_passwordreset.models import ResetPasswordToken, clear_expired, get_password_reset_token_expiry_time, \
    get_password_reset_lookup_field, clear_user_tokens
from django_rest_passwordreset.signals import reset_password_token_created, pre_password_reset, post_password_reset

User = get_user_model()


def create_registration_token(self, user):
    """
    A function which creasts a Registration Token for a new User

    User's must not have a useable password
    """

    # find a user by pk
    user = User.objects.get(pk=user)
    
    if user.eligible_for_reset(register_token=True):
        #clear the user's tokens
        clear_user_tokens(user)

        # create a new token 
        token = ResetPasswordToken.objects.create(
            user=user,
        )
        # send a signal that the password token was created
        # let whoever receives this signal handle sending the email for the password reset
        reset_password_token_created.send(sender=self, instance=self, reset_password_token=token)
    else:
        raise Exception("User not eligible for reset.")
