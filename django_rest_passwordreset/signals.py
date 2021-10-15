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
Signal arguments: user
"""
pre_password_reset = Signal()

"""
Signal arguments: user
"""
post_password_reset = Signal()
