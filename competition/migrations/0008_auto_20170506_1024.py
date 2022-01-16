# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0007_auto_20170501_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='away_team_winner_of',
            field=models.ForeignKey(related_name='match_next_away', blank=True, to='competition.Match', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='match',
            name='home_team_winner_of',
            field=models.ForeignKey(related_name='match_next_home', blank=True, to='competition.Match', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='match',
            name='away_team',
            field=models.ForeignKey(related_name='match_away_team', to='competition.Team', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='match',
            name='home_team',
            field=models.ForeignKey(related_name='match_home_team', to='competition.Team', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together=set([('name', 'sport')]),
        ),
    ]
