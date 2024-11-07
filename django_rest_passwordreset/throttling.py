from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import UserRateThrottle


__all__ = ("ResetPasswordRequestTokenThrottle",)


class ResetPasswordRequestTokenThrottle(UserRateThrottle):
    scope = "django-rest-passwordreset-request-token"
    default_rate = "3/day"

    def get_rate(self):
        try:
            return super().get_rate()
        except ImproperlyConfigured:
            return self.default_rate
