import django.dispatch

reset_password_token_created = django.dispatch.Signal(
    providing_args=["reset_password_token"],
)

pre_password_reset = django.dispatch.Signal(providing_args=["user"])

post_password_reset = django.dispatch.Signal(providing_args=["user"])
