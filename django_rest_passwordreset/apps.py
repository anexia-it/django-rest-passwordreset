from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoRestPasswordResetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_rest_passwordreset"
    verbose_name = _("Django REST PasswordReset")

    def ready(self) -> None:
        pass
