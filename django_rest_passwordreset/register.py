from django.contrib.auth import get_user_model
from django_rest_passwordreset.models import ResetPasswordToken, clear_user_tokens
from django_rest_passwordreset.signals import reset_password_token_created


User = get_user_model()

def create_registration_token(self, user):
    """
    A function which creasts a Registration Token for a new User

    User's must not have a useable password
    """

    # find a user by pk
    user = User.objects.get(pk=user)

    if user.eligible_for_reset(register_token=True):
        #clear the user's tokens
        clear_user_tokens(user)

        # create a new token 
        token = ResetPasswordToken.objects.create(
            user=user,
        )
        # send a signal that the password token was created
        # let whoever receives this signal handle sending the email for the password reset
        reset_password_token_created.send(sender=self, instance=self, reset_password_token=token)
    else:
        raise Exception("User not eligible for reset.")
