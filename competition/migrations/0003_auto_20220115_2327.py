# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-01-15 23:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0002_auto_20220115_2309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
