from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from rest_framework import status, exceptions
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django_rest_passwordreset.serializers import EmailSerializer, PasswordTokenSerializer, ResetTokenSerializer
from django_rest_passwordreset.models import ResetPasswordToken, clear_expired, get_password_reset_token_expiry_time, \
    get_password_reset_lookup_field
from django_rest_passwordreset.signals import reset_password_token_created, pre_password_reset, post_password_reset

User = get_user_model()

__all__ = [
    'ResetPasswordValidateToken',
    'ResetPasswordConfirm',
    'ResetPasswordRequestToken',
    'reset_password_validate_token',
    'reset_password_confirm',
    'reset_password_request_token'
]

HTTP_USER_AGENT_HEADER = getattr(settings, 'DJANGO_REST_PASSWORDRESET_HTTP_USER_AGENT_HEADER', 'HTTP_USER_AGENT')
HTTP_IP_ADDRESS_HEADER = getattr(settings, 'DJANGO_REST_PASSWORDRESET_IP_ADDRESS_HEADER', 'REMOTE_ADDR')


class ResetPasswordValidateToken(GenericAPIView):
    """
    An Api View which provides a method to verify that a token is valid
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = ResetTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        response_dict = dict({"status_code": None, "status": None, "message": None})
        # get token validation time
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        if reset_password_token is None:
            message = get_response_message("TOKEN_NOT_FOUND")
            response_dict.update({"status_code": 404, "status": "notfound", "message": message})
            return Response(response_dict, status=status.HTTP_404_NOT_FOUND)

        # check expiry date
        expiry_date = reset_password_token.created_at + timedelta(hours=password_reset_token_validation_time)

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            message = get_response_message("TOKEN_EXPIRED")
            response_dict.update({"status_code": 401, 'status': 'expired', "message": message})
            return Response(response_dict, status=status.HTTP_404_NOT_FOUND)

        message = get_response_message("TOKEN_VALID")
        response_dict.update({"status_code": 200, 'status': 'OK', "message": message})
        return Response(response_dict)


class ResetPasswordConfirm(GenericAPIView):
    """
    An Api View which provides a method to reset a password based on a unique token
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = PasswordTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        token = serializer.validated_data['token']
        response_dict = dict({"status_code": None, "message": None, "status": None})

        # get token validation time
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        if reset_password_token is None:
            message = get_response_message("TOKEN_NOT_FOUND")
            response_dict.update({"status_code": 404, 'status': 'notfound', "message": message})
            return Response(response_dict, status=status.HTTP_404_NOT_FOUND)

        # check expiry date
        expiry_date = reset_password_token.created_at + timedelta(hours=password_reset_token_validation_time)

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            message = get_response_message("TOKEN_EXPIRED")
            response_dict.update({"status_code": 404, 'status': 'expired', "message": message})

            return Response(response_dict, status=status.HTTP_404_NOT_FOUND)

        # change users password (if we got to this code it means that the user is_active)
        if reset_password_token.user.eligible_for_reset():
            pre_password_reset.send(sender=self.__class__, user=reset_password_token.user)
            try:
                # validate the password against existing validators
                validate_password(
                    password,
                    user=reset_password_token.user,
                    password_validators=get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)
                )
            except ValidationError as e:
                # raise a validation error for the serializer
                raise exceptions.ValidationError({
                    'password': e.messages
                })

            reset_password_token.user.set_password(password)
            reset_password_token.user.save()
            post_password_reset.send(sender=self.__class__, user=reset_password_token.user)

        # Delete all password reset tokens for this user
        ResetPasswordToken.objects.filter(user=reset_password_token.user).delete()

        # done
        message = get_response_message("PASSWORD_CHANGED")
        response_dict.update({"status_code": 200, "status": "OK", "message": message})

        return Response(response_dict)


class ResetPasswordRequestToken(GenericAPIView):
    """
    An Api View which provides a method to request a password reset token based on an e-mail address

    Sends a signal reset_password_token_created when a reset token was created
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = EmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # before we continue, delete all existing expired tokens
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # datetime.now minus expiry hours
        now_minus_expiry_time = timezone.now() - timedelta(hours=password_reset_token_validation_time)

        # delete all tokens where created_at < now - 24 hours
        clear_expired(now_minus_expiry_time)

        # find a user by email address (case insensitive search)
        users = User.objects.filter(**{'{}__iexact'.format(get_password_reset_lookup_field()): email})

        active_user_found = False

        # iterate over all users and check if there is any user that is active
        # also check whether the password can be changed (is useable), as there could be users that are not allowed
        # to change their password (e.g., LDAP user)
        for user in users:
            if user.eligible_for_reset():
                active_user_found = True

        # No active user found, raise a validation error
        # but not if DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE == True
        if not active_user_found and not getattr(settings, 'DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE', False):
            raise exceptions.ValidationError({

                'email': [_(
                    "We couldn't find an account associated with that email. Please try a different e-mail address.")],
            })

        # last but not least: iterate over all users that are active and can change their password
        # and create a Reset Password Token and send a signal with the created token
        for user in users:
            if user.eligible_for_reset():
                # define the token as none for now
                token = None

                # check if the user already has a token
                if user.password_reset_tokens.all().count() > 0:
                    # yes, already has a token, re-use this token
                    token = user.password_reset_tokens.all()[0]
                else:
                    # no token exists, generate a new token
                    token = ResetPasswordToken.objects.create(
                        user=user,
                        user_agent=request.META.get(HTTP_USER_AGENT_HEADER, ''),
                        ip_address=request.META.get(HTTP_IP_ADDRESS_HEADER, ''),
                    )
                # send a signal that the password token was created
                # let whoever receives this signal handle sending the email for the password reset
                reset_password_token_created.send(sender=self.__class__, instance=self, reset_password_token=token)
        # done
        message = get_response_message("PASSWORD_REQUEST_ACCEPT")
        return Response({"status_code": 200, "status": "OK", "message": message})


def get_response_message(message_key):
    """
        If message_key exists in settings.py, the corresponding message will be returned. Otherwise message_key
        is returned
        :param message_key: Key of the message in settings.py
        :return: status_message
    """

    status_message = getattr(settings, message_key, message_key)

    return status_message


reset_password_validate_token = ResetPasswordValidateToken.as_view()
reset_password_confirm = ResetPasswordConfirm.as_view()
reset_password_request_token = ResetPasswordRequestToken.as_view()
