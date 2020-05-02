# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_auto_incrementing_pk_field(apps, schema_editor):
    ResetPasswordToken = apps.get_model('django_rest_passwordreset', 'ResetPasswordToken')

    # Generate values for the new id column
    for i, o in enumerate(ResetPasswordToken.objects.all()):
        o.id = i + 1
        o.save()


def get_migrations_for_django_before_21():
    return [
        # add a new id field (without primary key information)
        migrations.AddField(
            model_name='resetpasswordtoken',
            name='id',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        # fill the new pk field
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


def get_migrations_for_django_21_and_newer():
    return [
        # remove primary key information from 'key' field
        migrations.AlterField(
            model_name='resetpasswordtoken',
            name='key',
            field=models.CharField(db_index=True, primary_key=False, max_length=64, unique=True, verbose_name='Key'),
        ),
        # add a new id field
        migrations.AddField(
            model_name='resetpasswordtoken',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
            preserve_default=False,
        ),
        migrations.RunPython(
            populate_auto_incrementing_pk_field,
            migrations.RunPython.noop
        ),
    ]


def get_migrations_based_on_django_version():
    """
    Returns the proper migrations based on the current Django Version

    Unfortunatley, Django 2.1 introduced a breaking change with switching PK from one model to another, see
    https://code.djangoproject.com/ticket/29790
    :return:
    """
    django_version = django.VERSION

    if (django_version[0] >= 2 and django_version[1] >= 1) or django_version[0] >= 3:
        return get_migrations_for_django_21_and_newer()

    return get_migrations_for_django_before_21()


class Migration(migrations.Migration):

    dependencies = [
        ('django_rest_passwordreset', '0001_initial',),
    ]

    operations = get_migrations_based_on_django_version()
