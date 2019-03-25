from django.core.management.base import BaseCommand
from django.utils import timezone

from django_rest_passwordreset.models import clear_expired, get_password_reset_token_expiry_time


class Command(BaseCommand):
    help = "Can be run as a cronjob or directly to clean out expired tokens"

    def handle(self, *args, **options):
        # datetime.now minus expiry hours
        now_minus_expiry_time = timezone.now() - timedelta(hours=get_password_reset_token_expiry_time())
        clear_expired(now_minus_expiry_time)
