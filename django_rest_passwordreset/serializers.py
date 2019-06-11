from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

__all__ = [
    'EmailSerializer',
    'UsernameSerializer',
    'PasswordTokenSerializer',
]


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField()


class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()