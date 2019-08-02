from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from rest_framework import serializers

__all__ = [
    'EmailSerializer',
    'PasswordTokenSerializer',
]


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()

    def __init__(self, *args, **kwargs):
        password_optional = kwargs.pop('password_optional', False)

        super(PasswordTokenSerializer, self).__init__(*args, **kwargs)

        if password_optional:
            self.fields['password'].required = False