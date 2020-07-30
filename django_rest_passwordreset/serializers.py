from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

__all__ = [
    'EmailSerializer',
    'PasswordTokenSerializer',
    'ResetTokenSerializer',
]


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()


class ResetTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
