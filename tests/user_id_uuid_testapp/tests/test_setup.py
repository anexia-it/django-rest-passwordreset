from django.apps import apps
from django.conf import settings
from django.db.models import UUIDField
from django.test import SimpleTestCase

from django_rest_passwordreset.models import ResetPasswordToken
from user_id_uuid_testapp.models import User


class TestSetup(SimpleTestCase):
    def test_installed_apps(self):
        self.assertIn("django_rest_passwordreset", settings.INSTALLED_APPS)

    def test_models(self):
        self.assertIs(
            apps.get_model("django_rest_passwordreset", "ResetPasswordToken"), ResetPasswordToken
        )
        self.assertIs(apps.get_model("user_id_uuid_testapp", "User"), User)
        for field in User._meta.fields:
            if field.name == "id":
                self.assertTrue(isinstance(field, UUIDField))
