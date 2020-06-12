from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.phonenumber import to_python
from rest_framework import serializers

from django_rest_passwordreset.models import get_password_reset_token_expiry_time
from . import models

__all__ = [
    'EmailSerializer',
    'PasswordTokenSerializer',
    'TokenSerializer',
]


class EmailSerializer(serializers.Serializer):
    email = serializers.CharField()

    def validate_email(self, value):
        phone_number = to_python(value)
        if phone_number and phone_number.is_valid():
            return value

        try:
            validator = EmailValidator()
            validator(value)
            return value
        except ValidationError:
            raise ValidationError(_('Enter a valid phone number or email address.'))



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
            raise Http404(_("The OTP password entered is not valid. Please check and try again."))

        # check expiry date
        expiry_date = reset_password_token.created_at + timedelta(
            hours=password_reset_token_validation_time)

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            raise Http404(_("The token has expired"))
        return data


class PasswordTokenSerializer(PasswordValidateMixin, serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()


class TokenSerializer(PasswordValidateMixin, serializers.Serializer):
    token = serializers.CharField()

