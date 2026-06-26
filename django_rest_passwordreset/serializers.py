from datetime import timedelta

from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from django_rest_passwordreset.models import get_password_reset_token_expiry_time
from . import models

__all__ = [
    'EmailSerializer',
    'PasswordTokenSerializer',
    'ResetTokenSerializer',
]

INVALID_TOKEN_ERROR = _("The OTP password entered is not valid. Please check and try again.")


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordValidateMixin:
    def validate(self, data):
        token = data.get('token')

        # get token validation time
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # find token
        try:
            reset_password_token = _get_object_or_404(models.ResetPasswordToken, key=token)
        except (TypeError, ValueError, ValidationError, Http404,
                models.ResetPasswordToken.DoesNotExist):
            raise Http404(INVALID_TOKEN_ERROR)

        # check expiry date
        expiry_date = reset_password_token.created_at + timedelta(
            hours=password_reset_token_validation_time)

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            raise Http404(INVALID_TOKEN_ERROR)
        return data


class PasswordTokenSerializer(PasswordValidateMixin, serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()


class ResetTokenSerializer(PasswordValidateMixin, serializers.Serializer):
    token = serializers.CharField()
