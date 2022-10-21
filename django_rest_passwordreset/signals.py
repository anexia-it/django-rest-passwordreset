from django.dispatch import Signal

__all__ = [
    'reset_password_token_created',
    'pre_password_reset',
    'post_password_reset',
]

"""
Signal arguments: instance, reset_password_token
"""
reset_password_token_created = Signal()

"""
Signal arguments: user, reset_password_token
"""
pre_password_reset = Signal()

"""
Signal arguments: user, reset_password_token
"""
post_password_reset = Signal()
