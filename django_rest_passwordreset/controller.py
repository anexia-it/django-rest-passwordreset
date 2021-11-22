import unicodedata
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    get_password_validators,
    validate_password,
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ninja_extra import APIController, exceptions, route, router

from .models import (
    ResetPasswordToken,
    clear_expired,
    get_password_reset_lookup_field,
    get_password_reset_token_expiry_time,
)
from .schema import EmailSerializer, PasswordTokenSerializer, ResetTokenSerializer
from .signals import (
    post_password_reset,
    pre_password_reset,
    reset_password_token_created,
)

User = get_user_model()

__all__ = ["ResetPasswordController"]

HTTP_USER_AGENT_HEADER = getattr(
    settings, "DJANGO_REST_PASSWORDRESET_HTTP_USER_AGENT_HEADER", "HTTP_USER_AGENT"
)
HTTP_IP_ADDRESS_HEADER = getattr(
    settings, "DJANGO_REST_PASSWORDRESET_IP_ADDRESS_HEADER", "REMOTE_ADDR"
)


def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    normalized1 = unicodedata.normalize("NFKC", s1)
    normalized2 = unicodedata.normalize("NFKC", s2)

    return normalized1.casefold() == normalized2.casefold()


@router("password_reset/", tags=["Password Reset"])
class ResetPasswordController(APIController):
    auto_import = False

    @route.post("validate_token/", url_name="reset-password-validate")
    def validate_token(self, reset_token: ResetTokenSerializer):
        """
        An Api View which provides a method to verify that a token is valid
        """
        return self.create_response({"status": "OK"})

    @route.post("confirm/", url_name="reset-password-confirm")
    def password_confirm(self, password_token: PasswordTokenSerializer):
        password = password_token.password
        token = password_token.token

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        # change users password (if we got to this code it means that the user is_active)
        if reset_password_token.user.eligible_for_reset():
            pre_password_reset.send(
                sender=self.__class__, user=reset_password_token.user
            )
            try:
                # validate the password against existing validators
                validate_password(
                    password,
                    user=reset_password_token.user,
                    password_validators=get_password_validators(
                        settings.AUTH_PASSWORD_VALIDATORS
                    ),
                )
            except ValidationError as e:
                # raise a validation error for the serializer
                raise exceptions.ValidationError({"password": e.messages})

            reset_password_token.user.set_password(password)
            reset_password_token.user.save()
            post_password_reset.send(
                sender=self.__class__, user=reset_password_token.user
            )

        # Delete all password reset tokens for this user
        ResetPasswordToken.objects.filter(user=reset_password_token.user).delete()

        return self.create_response({"status": "OK"})

    @route.post("", url_name="reset-password-request")
    def password_request_token(self, email_data: EmailSerializer):
        email = email_data.email

        # before we continue, delete all existing expired tokens
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # datetime.now minus expiry hours
        now_minus_expiry_time = timezone.now() - timedelta(
            hours=password_reset_token_validation_time
        )

        # delete all tokens where created_at < now - 24 hours
        clear_expired(now_minus_expiry_time)

        # find a user by email address (case insensitive search)
        users = User.objects.filter(
            **{"{}__iexact".format(get_password_reset_lookup_field()): email}
        )

        active_user_found = False

        # iterate over all users and check if there is any user that is active
        # also check whether the password can be changed (is useable), as there could be users that are not allowed
        # to change their password (e.g., LDAP user)
        for user in users:
            if user.eligible_for_reset():
                active_user_found = True
                break

        # No active user found, raise a validation error
        # but not if DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE == True
        if not active_user_found and not getattr(
            settings, "DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE", False
        ):
            raise exceptions.ValidationError(
                {
                    "email": [
                        _(
                            "We couldn't find an account associated with that email. Please try a different e-mail address."
                        )
                    ],
                }
            )

        # last but not least: iterate over all users that are active and can change their password
        # and create a Reset Password Token and send a signal with the created token
        for user in users:
            if user.eligible_for_reset() and _unicode_ci_compare(
                email, getattr(user, get_password_reset_lookup_field())
            ):
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
                        user_agent=self.context.request.META.get(
                            HTTP_USER_AGENT_HEADER, ""
                        ),
                        ip_address=self.context.request.META.get(
                            HTTP_IP_ADDRESS_HEADER, ""
                        ),
                    )
                # send a signal that the password token was created
                # let whoever receives this signal handle sending the email for the password reset
                reset_password_token_created.send(
                    sender=self.__class__, instance=self, reset_password_token=token
                )
        # done
        return self.create_response({"status": "OK"})
