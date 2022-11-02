# Django Rest Password Reset

[![PyPI version](https://img.shields.io/pypi/v/django-rest-passwordreset.svg)](https://pypi.org/project/django-rest-passwordreset/)
[![build-and-test actions status](https://github.com/anexia-it/django-rest-passwordreset/workflows/build-and-test/badge.svg)](https://github.com/anexia-it/django-rest-passwordreset/actions)
[![Codecov](https://img.shields.io/codecov/c/gh/anexia-it/django-rest-passwordreset)](https://codecov.io/gh/anexia-it/django-rest-passwordreset)

This python package provides a simple password reset strategy for django rest framework, where users can request password 
reset tokens via their registered e-mail address.

The main idea behind this package is to not make any assumptions about how the token is delivered to the end-user (e-mail, text-message, etc...).
Instead, this package provides a signal that can be reacted on (e.g., by sending an e-mail or a text message).

This package basically provides two REST endpoints:

* Request a token
* Verify (confirm) a token (and change the password)

## Quickstart

1. Install the package from pypi using pip:
```bash
pip install django-rest-passwordreset
```

2. Add ``django_rest_passwordreset`` to your ``INSTALLED_APPS`` (after ``rest_framework``) within your Django settings file:
```python
INSTALLED_APPS = (
    ...
    'django.contrib.auth',
    ...
    'rest_framework',
    ...
    'django_rest_passwordreset',
    ...
)
```

3. This package stores tokens in a separate database table (see [django_rest_passwordreset/models.py](django_rest_passwordreset/models.py)). Therefore, you have to run django migrations:
```bash
python manage.py migrate
```

4. This package provides three endpoints, which can be included by including ``django_rest_passwordreset.urls`` in your ``urls.py`` as follows:
```python
from django.urls import path, include

urlpatterns = [
    ...
    path(r'^api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    ...
]
```
**Note**: You can adapt the URL to your needs.

### Endpoints

The following endpoints are provided:

 * `POST ${API_URL}/` - request a reset password token by using the ``email`` parameter
 * `POST ${API_URL}/confirm/` - using a valid ``token``, the users password is set to the provided ``password``
 * `POST ${API_URL}/validate_token/` - will return a 200 if a given ``token`` is valid
 
where `${API_URL}/` is the url specified in your *urls.py* (e.g., `api/password_reset/` as in the example above)

 
### Signals

* ``reset_password_token_created(sender, instance, reset_password_token)`` Fired when a reset password token is generated
* ``pre_password_reset(sender, user, reset_password_token)`` - fired just before a password is being reset
* ``post_password_reset(sender, user, reset_password_token)`` - fired after a password has been reset

### Example for sending an e-mail

1. Create two new django templates: `email/user_reset_password.html` and `email/user_reset_password.txt`. Those templates will contain the e-mail message sent to the user, aswell as the password reset link (or token).
Within the templates, you can access the following context variables: `current_user`, `username`, `email`, `reset_password_url`. Feel free to adapt this to your needs.

2. Add the following code, which contains a Django Signal Receiver (`@receiver(...)`), to your application. Take care where to put this code, as it needs to be executed by the python interpreter (see the section *The `reset_password_token_created` signal is not fired* below, aswell as [this part of the django documentation](https://docs.djangoproject.com/en/1.11/topics/signals/#connecting-receiver-functions) and [How to Create Django Signals Tutorial](https://simpleisbetterthancomplex.com/tutorial/2016/07/28/how-to-create-django-signals.html) for more information).
```python
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse

from django_rest_passwordreset.signals import reset_password_token_created


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    context = {
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': "{}?token={}".format(
            instance.request.build_absolute_uri(reverse('password_reset:reset-password-confirm')),
            reset_password_token.key)
    }

    # render email text
    email_html_message = render_to_string('email/user_reset_password.html', context)
    email_plaintext_message = render_to_string('email/user_reset_password.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(title="Some website title"),
        # message:
        email_plaintext_message,
        # from:
        "noreply@somehost.local",
        # to:
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()

```

3. You should now be able to use the endpoints to request a password reset token via your e-mail address. 
If you want to test this locally, I recommend using some kind of fake mailserver (such as maildump).



# Configuration / Settings

The following settings can be set in Django ``settings.py`` file:

* `DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME` - time in hours about how long the token is active (Default: 24)

  **Please note**: expired tokens are automatically cleared based on this setting in every call of ``ResetPasswordRequestToken.post``.

* `DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE` - will cause a 200 to be returned on `POST ${API_URL}/reset_password/`
  even if the user doesn't exist in the databse (Default: False) 

* `DJANGO_REST_MULTITOKENAUTH_REQUIRE_USABLE_PASSWORD` - allows password reset for a user that does not 
  [have a usable password](https://docs.djangoproject.com/en/2.2/ref/contrib/auth/#django.contrib.auth.models.User.has_usable_password) (Default: True)

## Custom Email Lookup

By default, `email` lookup is used to find the user instance. You can change that by adding 
```python
DJANGO_REST_LOOKUP_FIELD = 'custom_email_field'
```
into Django settings.py file.

## Custom Remote IP Address and User Agent Header Lookup

If your setup demands that the IP adress of the user is in another header (e.g., 'X-Forwarded-For'), you can configure that (using Django Request Headers):

```python
DJANGO_REST_PASSWORDRESET_IP_ADDRESS_HEADER = 'HTTP_X_FORWARDED_FOR'
```

The same is true for the user agent:

```python
HTTP_USER_AGENT_HEADER = 'HTTP_USER_AGENT'
```

## Custom Token Generator

By default, a random string token of length 10 to 50 is generated using the ``RandomStringTokenGenerator`` class.
This library offers a possibility to configure the params of ``RandomStringTokenGenerator`` as well as switch to
another token generator, e.g. ``RandomNumberTokenGenerator``. You can also generate your own token generator class.

You can change that by adding 
```python
DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": ...,
    "OPTIONS": {...}
}
```
into Django settings.py file.


### RandomStringTokenGenerator
This is the default configuration. 
```python
DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": "django_rest_passwordreset.tokens.RandomStringTokenGenerator"
}
```

You can configure the length as follows:
```python
DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": "django_rest_passwordreset.tokens.RandomStringTokenGenerator",
    "OPTIONS": {
        "min_length": 20,
        "max_length": 30
    }
}
```

It uses `os.urandom()` to generate a good random string.
   

### RandomNumberTokenGenerator
```python
DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": "django_rest_passwordreset.tokens.RandomNumberTokenGenerator"
}
```

You can configure the minimum and maximum number as follows:
```python
DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": "django_rest_passwordreset.tokens.RandomNumberTokenGenerator",
    "OPTIONS": {
        "min_number": 1500,
        "max_number": 9999
    }
}
```

It uses `random.SystemRandom().randint()` to generate a good random number.


### Write your own Token Generator

Please see [token_configuration/django_rest_passwordreset/tokens.py](token_configuration/django_rest_passwordreset/tokens.py) for example implementation of number and string token generator.

The basic idea is to create a new class that inherits from BaseTokenGenerator, takes arbitrary arguments (`args` and `kwargs`)
in the ``__init__`` function as well as implementing a `generate_token` function.

```python
from django_rest_passwordreset.tokens import BaseTokenGenerator


class RandomStringTokenGenerator(BaseTokenGenerator):
    """
    Generates a random string with min and max length using os.urandom and binascii.hexlify
    """

    def __init__(self, min_length=10, max_length=50, *args, **kwargs):
        self.min_length = min_length
        self.max_length = max_length

    def generate_token(self, *args, **kwargs):
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        # determine the length based on min_length and max_length
        length = random.randint(self.min_length, self.max_length)

        # generate the token using os.urandom and hexlify
        return binascii.hexlify(
            os.urandom(self.max_length)
        ).decode()[0:length]
```


## Compatibility Matrix

This library should be compatible with the latest Django and Django Rest Framework Versions. For reference, here is
a matrix showing the guaranteed and tested compatibility.

django-rest-passwordreset Version | Django Versions | Django Rest Framework Versions | Python |
--------------------------------- | --------------- | ------------------------------ | ------ |
0.9.7 | 1.8, 1.11, 2.0, 2.1 | 3.6 - 3.9 | 2.7
1.0 | 1.11, 2.0, 2.2 | 3.6 - 3.9 | 2.7
1.1 | 1.11, 2.2 | 3.6 - 3.9 | 2.7
1.2 | 2.2, 3.0, 3.1 | 3.10, 3.11 | 3.5 - 3.8
1.3 | 3.2, 4.0, 4.1 | 3.12, 3.13 | 3.7 - 3.10


## Documentation / Browsable API

This package supports the [DRF auto-generated documentation](https://www.django-rest-framework.org/topics/documenting-your-api/) (via `coreapi`) as well as the [DRF browsable API](https://www.django-rest-framework.org/topics/browsable-api/).

To add the endpoints to the browsable API, you can use a helper function in your `urls.py` file:
```python
from rest_framework.routers import DefaultRouter
from django_rest_passwordreset.urls import add_reset_password_urls_to_router

router = DefaultRouter()
add_reset_password_urls_to_router(router, base_path='api/auth/passwordreset')
```

Alternatively you can import the ViewSets manually and customize the routes for your setup:
```python
from rest_framework.routers import DefaultRouter
from django_rest_passwordreset.views import ResetPasswordValidateTokenViewSet, ResetPasswordConfirmViewSet, \
    ResetPasswordRequestTokenViewSet

router = DefaultRouter()
router.register(
    r'api/auth/passwordreset/validate_token',
    ResetPasswordValidateTokenViewSet,
    basename='reset-password-validate'
)
router.register(
    r'api/auth/passwordreset/confirm',
    ResetPasswordConfirmViewSet,
    basename='reset-password-confirm'
)
router.register(
    r'api/auth/passwordreset/',
    ResetPasswordRequestTokenViewSet,
    basename='reset-password-request'
)
```

![drf_browsable_email_validation](docs/browsable_api_email_validation.png "Browsable API E-Mail Validation")

![drf_browsable_password_validation](docs/browsable_api_password_validation.png "Browsable API E-Mail Validation")

![coreapi_docs](docs/coreapi_docs.png "Core API Docs")


## Known Issues / FAQ

### Django 2.1 Migrations - Multiple Primary keys for table ...
Django 2.1 introduced a breaking change for migrations (see [Django Issue #29790](https://code.djangoproject.com/ticket/29790)). We therefore had to rewrite the migration [0002_pk_migration.py](django_rest_passwordreset/migrations/0002_pk_migration.py) such that it covers Django versions before (`<`) 2.1 and later (`>=`) 2.1.

Some information is written down in Issue #8.

### The `reset_password_token_created` signal is not fired
You need to make sure that the code with `@receiver(reset_password_token_created)` is executed by the python interpreter. To ensure this, you have two options:

1. Put the code at a place that is automatically loaded by Django (e.g., models.py, views.py), or

2. Import the file that contains the signal within your app.py `ready` function:

  *some_app/signals.py*
  ```python
  from django.core.mail import EmailMultiAlternatives
  from django.dispatch import receiver
  from django.template.loader import render_to_string
  from django.urls import reverse

  from django_rest_passwordreset.signals import reset_password_token_created


  @receiver(reset_password_token_created)
  def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
      # ...
  ```
  
  *some_app/app.py*
  ```python
  from django.apps import AppConfig

  class SomeAppConfig(AppConfig):
      name = 'your_django_project.some_app'
      verbose_name = 'Some App'

      def ready(self):
          import your_django_project.some_app.signals  # noqa
  ```
  
  *some_app/__init__.py*
  ```python
  default_app_config = 'your_django_project.some_app.SomeAppConfig'
  ```

### MongoDB not working

Apparently, the following piece of code in the Django Model prevents MongodB from working:

```python
 id = models.AutoField( 
     primary_key=True 
 ) 
```

See issue #49 for details.

## Contributions

This library tries to follow the unix philosophy of "do one thing and do it well" (which is providing a basic password reset endpoint for Django Rest Framework). Contributions are welcome in the form of pull requests and issues! If you create a pull request, please make sure that you are not introducing breaking changes. 

## Tests

See folder [tests/](tests/). Basically, all endpoints are covered with multiple
unit tests.

Follow below instructions to run the tests.
You may exchange the installed Django and DRF versions according to your requirements. 
:warning: Depending on your local environment settings you might need to explicitly call `python3` instead of `python`.
```bash
# install dependencies
python -m pip install --upgrade pip
pip install -r tests/requirements.txt

# setup environment
pip install -e .

# run tests
cd tests && python manage.py test
```

## Release on PyPi

To release this package on pypi, the following steps are used:

```bash
rm -rf dist/ build/
python setup.py sdist
twine upload dist/*
```
