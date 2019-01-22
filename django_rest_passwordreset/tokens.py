import os
import binascii
import random
from importlib import import_module

from django.conf import settings


def get_token_generator():
    """
    Returns the token generator class based on the configuration in DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG.CLASS and
    DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG.OPTIONS
    :return:
    """
    # by default, we are using the String Token Generator
    token_class = RandomStringTokenGenerator
    options = {}

    # get the settings object
    DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = getattr(settings, 'DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG', None)

    # check if something is in the settings object, and work with it
    if DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG:
        if "CLASS" in DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG:
            class_path_name = DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG["CLASS"]
            module_name, class_name = class_path_name.rsplit('.', 1)

            mod = import_module(module_name)
            token_class = getattr(mod, class_name)

        if "OPTIONS" in DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG:
            options = DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG["OPTIONS"]

    # initialize the token class and pass options
    return token_class(**options)


class BaseTokenGenerator:
    """
    Base Class for the Token Generators

    - Can take arbitrary args/kwargs and work with those
    - Needs to implement the "generate_token" Method
    """
    def __init__(self, *args, **kwargs):
        pass

    def generate_token(self, *args, **kwargs):
        raise NotImplementedError


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


class RandomNumberTokenGenerator(BaseTokenGenerator):
    """
    Generates a random number
    """
    def __init__(self, min_number=10000, max_number=99999, *args, **kwargs):
        self.min_number = min_number
        self.max_number = max_number

    def generate_token(self, *args, **kwargs):
        # generate a random number between min_number and max_number
        return str(random.randint(self.min_number, self.max_number))
