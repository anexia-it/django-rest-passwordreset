from ninja_extra import NinjaExtraAPI

from django_rest_passwordreset.controller import ResetPasswordController

api = NinjaExtraAPI(urls_namespace="password_reset")
api.register_controllers(ResetPasswordController)
