from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from rest_framework.settings import api_settings
from rest_framework.throttling import UserRateThrottle


__all__ = ("ResetPasswordRequestTokenThrottle", "get_password_reset_request_token_throttle_classes")


class ResetPasswordRequestTokenThrottle(UserRateThrottle):
    scope = "django-rest-passwordreset-request-token"
    default_rate = "3/day"

    def get_rate(self):
        try:
            return super().get_rate()
        except ImproperlyConfigured:
            return self.default_rate


def _resolve_throttle_class(throttle_class):
    if isinstance(throttle_class, str):
        return import_string(throttle_class)
    return throttle_class


def get_password_reset_request_token_throttle_classes():
    throttle_classes = getattr(settings, 'DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES', None)

    if throttle_classes is None:
        return (ResetPasswordRequestTokenThrottle,)

    if isinstance(throttle_classes, str):
        throttle_classes = (throttle_classes,)

    if not throttle_classes:
        return tuple(api_settings.DEFAULT_THROTTLE_CLASSES)

    return tuple(_resolve_throttle_class(throttle_class) for throttle_class in throttle_classes)
