# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='state',
            field=models.IntegerField(default=1, choices=[(0, b'Pending'), (1, b'Active'), (2, b'finished')]),
        ),
        migrations.AddField(
            model_name='tournament',
            name='winner',
            field=models.ForeignKey(related_name='+', blank=True, to='competition.Participant', null=True, on_delete=models.CASCADE),
        ),
    ]
