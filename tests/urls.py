""" Tests App URL Config """
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("api/password_reset/", include('django_rest_passwordreset.urls', namespace='password_reset')),
    path("admin/", admin.site.urls),
]
