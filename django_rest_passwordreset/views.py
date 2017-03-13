from datetime import timedelta
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from rest_framework import parsers, renderers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django_rest_passwordreset.serializers import EmailSerializer, PasswordTokenSerializer
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.signals import reset_password_token_created, pre_password_reset, post_password_reset


def get_password_reset_token_expiry_time():
    """
    Returns the password reset token expirty time in hours (default: 24)
    Set Django SETTINGS.DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME to overwrite this time
    :return: expiry time
    """
    # get token validation time
    return getattr(settings, 'DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME', 24)


class ResetPasswordConfirm(APIView):
    """
    An Api View which provides a method to reset a password based on a unique token
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = PasswordTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        token = serializer.validated_data['token']

        # get token validation time
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        if reset_password_token is None:
            return Response({'status': 'notfound'}, status=status.HTTP_404_NOT_FOUND)

        # check expiry date
        expiry_date = reset_password_token.created_at + timedelta(hours=password_reset_token_validation_time)

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            return Response({'status': 'expired'}, status=status.HTTP_404_NOT_FOUND)

        # change users password
        if reset_password_token.user.has_usable_password():
            pre_password_reset.send(sender=self.__class__, user=reset_password_token.user)
            reset_password_token.user.set_password(password)
            reset_password_token.user.save()
            post_password_reset.send(sender=self.__class__, user=reset_password_token.user)

        # Delete all password reset tokens for this user
        ResetPasswordToken.objects.filter(user=reset_password_token.user).delete()

        return Response({'status': 'OK'})


class ResetPasswordRequestToken(APIView):
    """
    An Api View which provides a method to request a password reset token based on an e-mail address

    Sends a signal reset_password_token_created when a reset token was created
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
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
        ResetPasswordToken.objects.filter(created_at__lte=now_minus_expiry_time).delete()

        # find a user by email address (case insensitive search)
        users = User.objects.filter(email__iexact=email)

        active_user_found = False

        # iterate over all users and check if there is any user that is active
        # also check whether the password can be changed (is useable), as there could be users that are not allowed
        # to change their password (e.g., LDAP user)
        for user in users:
            if user.is_active and user.has_usable_password():
                active_user_found = True

        # No active user found, raise a validation error
        if not active_user_found:
            raise ValidationError({
                'email': ValidationError(
                    _("There is no active user associated with this e-mail address or the password can not be changed"),
                    code='invalid')}
            )

        # last but not least: iterate over all users that are active and can change their password
        # and create a Reset Password Token and send a signal with the created token
        for user in users:
            if user.is_active and user.has_usable_password():
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
                        user_agent=request.META['HTTP_USER_AGENT'],
                        ip_address=request.META['REMOTE_ADDR']
                    )
                # send a signal that the password token was created
                # let whoever receives this signal handle sending the email for the password reset
                reset_password_token_created.send(sender=self.__class__, reset_password_token=token)
        # done
        return Response({'status': 'OK'})


reset_password_confirm = ResetPasswordConfirm.as_view()
reset_password_request_token = ResetPasswordRequestToken.as_view()
