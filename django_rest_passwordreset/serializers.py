from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

__all__ = [
    'EmailSerializer',
    'PasswordTokenSerializer',
    'TokenSerializer',
]

def check_phone(phone):
    import phonenumbers
    try:
        phone_obj = phonenumbers.parse(phone, None)
        return True, phone_obj
    except phonenumbers.phonenumberutil.NumberParseException as e:
        return False, e._msg

class EmailPhoneSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone"):
            raise serializers.ValidationError('Please provide Email or Phone Number')
        return attrs

    def validate_phone(self, attrs):
        validate_phone = check_phone(attrs)
        if not validate_phone[0]:
            raise serializers.ValidationError(validate_phone[1])
        return attrs


class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})
    token = serializers.CharField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()
