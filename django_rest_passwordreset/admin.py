""" contains basic admin views for MultiToken """
from django.contrib import admin
from django_rest_passwordreset.models import ResetPasswordToken


@admin.register(ResetPasswordToken)
class ResetPasswordTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at', 'ip_address', 'user_agent')
