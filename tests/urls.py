""" Tests App URL Config """
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

from .api import api

print(f"Was here: {__name__}")
urlpatterns = [
    path("api/password_reset/", api.urls),
    path("admin/", admin.site.urls),
]
