from datetime import timedelta

from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django_rest_passwordreset.models import get_password_reset_token_expiry_time
from django.utils import timezone

from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from . import models

__all__ = [
    'EmailSerializer',
    'PasswordTokenSerializer',
    'TokenSerializer',
]


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordValidateMixin:
    def validate(self, data):
        token = data.get('token')

        # get token validation time
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # find token
        reset_password_token = get_object_or_404(models.ResetPasswordToken, key=token)

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

