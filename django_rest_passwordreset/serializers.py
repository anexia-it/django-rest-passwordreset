from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.utils.serializer_helpers import BindingDict
from django.utils.functional import cached_property
from django_rest_passwordreset.models import get_password_reset_lookup_field

__all__ = [
    'LookupSerializer',
    'PasswordTokenSerializer',
    'TokenSerializer',
]

class LookupSerializer(serializers.Serializer):
    @cached_property
    def fields(self):
        fields = BindingDict(self)
        lookup_field = get_password_reset_lookup_field()
        fields[lookup_field] = serializers.CharField()
        return fields

class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()
