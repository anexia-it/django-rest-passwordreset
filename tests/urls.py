""" Tests App URL Config """
from django.conf.urls import url, include
from django.contrib import admin


urlpatterns = [
    url(r'^api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    url(r'^admin/', admin.site.urls),
]
