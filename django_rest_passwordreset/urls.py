""" URL Configuration for core auth """
from django.urls import path

from django_rest_passwordreset.views import ResetPasswordConfirmViewSet, ResetPasswordRequestTokenViewSet, \
    ResetPasswordValidateTokenViewSet, reset_password_confirm, reset_password_request_token, \
    reset_password_validate_token

app_name = 'password_reset'


def add_reset_password_urls_to_router(router, base_path=''):
    router.register(
        base_path + "/validate_token",
        ResetPasswordValidateTokenViewSet,
        basename='reset-password-validate'
    )
    router.register(
        base_path + "/confirm",
        ResetPasswordConfirmViewSet,
        basename='reset-password-confirm'
    )
    router.register(
        base_path,
        ResetPasswordRequestTokenViewSet,
        basename='reset-password-request'
    )


urlpatterns = [
    path("validate_token/", reset_password_validate_token, name="reset-password-validate"),
    path("confirm/", reset_password_confirm, name="reset-password-confirm"),
    path("", reset_password_request_token, name="reset-password-request"),
]
