from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()

    def validate_password(self, password):
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return password
