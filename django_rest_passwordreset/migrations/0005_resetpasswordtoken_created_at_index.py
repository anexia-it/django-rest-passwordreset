# Generated for django-rest-passwordreset: index ResetPasswordToken.created_at to
# speed up expired-token cleanup (`created_at__lte` range scan used by the
# `clearresetpasswodtokens` management command and the request-token endpoint).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_rest_passwordreset', '0004_alter_resetpasswordtoken_user_agent'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='resetpasswordtoken',
            index=models.Index(fields=['created_at'], name='drpr_token_created_at_idx'),
        ),
    ]
