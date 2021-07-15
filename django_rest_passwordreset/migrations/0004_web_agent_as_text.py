# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2021-07-15 23:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_rest_passwordreset', '0003_allow_blank_and_null_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resetpasswordtoken',
            name='user_agent',
            field=models.TextField(blank=True, default='', verbose_name='HTTP User Agent'),
        ),
    ]
