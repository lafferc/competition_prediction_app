# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0008_auto_20170506_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='away_team',
            field=models.ForeignKey(related_name='match_away_team', blank=True, to='competition.Team', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='match',
            name='home_team',
            field=models.ForeignKey(related_name='match_home_team', blank=True, to='competition.Team', null=True, on_delete=models.CASCADE),
        ),
    ]
