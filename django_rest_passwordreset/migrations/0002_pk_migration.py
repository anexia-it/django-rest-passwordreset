# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_auto_incrementing_pk_field(apps, schema_editor):
    ResetPasswordToken = apps.get_model('django_rest_passwordreset', 'ResetPasswordToken')

    # Generate values for the new id column
    for i, o in enumerate(ResetPasswordToken.objects.all()):
        o.id = i + 1
        o.save()


class Migration(migrations.Migration):

    dependencies = [
        ('django_rest_passwordreset', '0001_initial',),
    ]

    operations = [
        migrations.AddField(
            model_name='resetpasswordtoken',
            name='id',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.RunPython(
            populate_auto_incrementing_pk_field,
            migrations.RunPython.noop
        ),
        # add primary key information to id field
        migrations.AlterField(
            model_name='resetpasswordtoken',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False)
        ),
        # remove primary key information from 'key' field
        migrations.AlterField(
            model_name='resetpasswordtoken',
            name='key',
            field=models.CharField(db_index=True, max_length=64, unique=True, verbose_name='Key'),
        ),
    ]
