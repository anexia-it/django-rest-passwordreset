"""
Django settings for github action postgres tests.

"""

from settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "HOST": "localhost",
        "PORT": "5432",
        "NAME": "postgres",
        "USER": "user",
        "PASSWORD": "password",
    }
}
