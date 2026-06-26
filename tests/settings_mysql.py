"""
Django settings for github action mysql tests.

"""

from settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        # Django's test runner CREATEs/DROPs the test database
        # (``test_<NAME>``), which requires CREATE privileges. The app user
        # created by the MySQL service image only has rights on ``drpr_test``
        # itself, so connect as root for the test run.
        "NAME": "drpr_test",
        "USER": "root",
        "PASSWORD": "rootpassword",
    }
}