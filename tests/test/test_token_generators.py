from django.test import TestCase
from django.conf import settings

from django_rest_passwordreset.tokens import RandomStringTokenGenerator, RandomNumberTokenGenerator, get_token_generator


class TokenGeneratorTestCase(TestCase):
    """
    Tests that the token generators work as expected
    """
    def setUp(self):
        pass

    def test_string_token_generator(self):
        token_generator = RandomStringTokenGenerator(min_length=10, max_length=15)

        tokens = []

        # generate 100 tokens
        for i in range(0, 100):
            tokens.append(token_generator.generate_token())

        # validate that those 100 tokens are unique
        unique_tokens = list(set(tokens))

        self.assertEquals(
            len(tokens), len(unique_tokens), msg="StringTokenGenerator must create unique tokens"
        )
        ################################################################################################################
        # Please note: The above does not guarantee true randomness, it's just a necessity to make sure that we do not
        # return the same token all the time (by accident)
        ################################################################################################################

        # validate that each token is between 10 and 15 characters
        for token in tokens:
            self.assertGreaterEqual(
                len(token), 10, msg="StringTokenGenerator must create tokens of min. length of 10"
            )
            self.assertLessEqual(
                len(token), 15, msg="StringTokenGenerator must create tokens of max. length of 15"
            )

    def test_number_token_generator(self):
        token_generator = RandomNumberTokenGenerator(min_number=1000000000, max_number=9999999999)

        tokens = []

        # generate 100 tokens
        for i in range(0, 100):
            tokens.append(token_generator.generate_token())

        # validate that those 100 tokens are unique
        unique_tokens = list(set(tokens))

        self.assertEquals(
            len(tokens), len(unique_tokens), msg="RandomNumberTokenGenerator must create unique tokens"
        )
        ################################################################################################################
        # Please note: The above does not guarantee true randomness, it's just a necessity to make sure that we do not
        # return the same token all the time (by accident)
        ################################################################################################################

        # validate that each token is a number between 100000 and 999999
        for token in tokens:
            is_number = False
            try:
                num = int(token)
                is_number = True
            except:
                is_number = False

            self.assertEquals(is_number, True, msg="RandomNumberTokenGenerator must return a number, but returned "
                                                   + token)

            self.assertGreaterEqual(num, 1000000000, msg="RandomNumberTokenGenerator must return a number greater or equal to 1000000000")
            self.assertLess(num, 9999999999, msg="RandomNumberTokenGenerator must return a number less or equal to 9999999999")

    def test_generate_token_generator_from_empty_settings(self):
        """
        If there is no setting for DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG, a RandomStringTokenGenerator should
        be created automatically by get_token_generator()
        :return:
        """
        # patch settings
        settings.DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = None

        token_generator = get_token_generator()

        self.assertEquals(
            token_generator.__class__, RandomStringTokenGenerator,
            msg="If no class is set in DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG, a RandomStringTokenGenerator should"
                "be created"
        )

    def test_generate_token_generator_from_settings_string_token_generator(self):
        """
        Checks if the get_token_generator() function uses the "CLASS" setting in DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG
        :return:
        """
        # patch settings
        settings.DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
            "CLASS": "django_rest_passwordreset.tokens.RandomStringTokenGenerator"
        }

        token_generator = get_token_generator()

        self.assertEquals(
            token_generator.__class__, RandomStringTokenGenerator,
            msg="get_token_generator() should return an instance of RandomStringTokenGenerator "
                "if configured in settings"
        )

    def test_generate_token_generator_from_settings_number_token_generator(self):
        """
        Checks if the get_token_generator() function uses the "CLASS" setting in DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG
        :return:
        """
        # patch settings
        settings.DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
            "CLASS": "django_rest_passwordreset.tokens.RandomNumberTokenGenerator"
        }

        token_generator = get_token_generator()

        self.assertEquals(
            token_generator.__class__, RandomNumberTokenGenerator,
            msg="get_token_generator() should return an instance of RandomNumberTokenGenerator "
                "if configured in settings"
        )
