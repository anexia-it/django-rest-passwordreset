# Django Rest Password Reset
This django app provides a password reset strategy for django rest framework, where users can request password 
reset tokens via their registered e-mail address.

## How to use

Django settings file:
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


Django url settings:
```python
from django.conf.urls import url, include


urlpatterns = [
    ...
    url(r'^api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    ...
]    
```


The following endpoints are provided:

 * `reset_password` - request a reset password token by using the ``email`` parameter
 * `reset_password/confirm` - using a valid ``token``, the users password is set to the provided ``password``
 
## Signals

* ``reset_password_token_created(reset_password_token)`` Fired when a reset password token is generated
* ``pre_password_reset(user)`` - fired just before a password is being reset
* ``post_password_reset(user)`` - fired after a password has been reset

## Tests

See folder [tests/](tests/). Basically, all endpoints are covered with multiple
unit tests.

Use this code snippet to run tests:
```bash
pip install -r requirements_test.txt
python setup.py install
cd tests
python manage.py test
```
