# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('match_id', models.IntegerField()),
                ('kick_off', models.DateTimeField()),
                ('score', models.IntegerField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entered', models.DateTimeField(auto_now_add=True)),
                ('prediction', models.DecimalField(default=0, max_digits=5, decimal_places=2)),
                ('score', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
                ('late', models.BooleanField(default=False)),
                ('match', models.ForeignKey(to='competition.Match', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Sport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('code', models.CharField(unique=True, max_length=3)),
                ('sport', models.ForeignKey(to='competition.Sport', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('bonus', models.DecimalField(default=2, null=True, max_digits=5, decimal_places=2, blank=True)),
                ('late_get_bonus', models.BooleanField(default=True)),
                ('participants', models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='competition.Participant')),
                ('sport', models.ForeignKey(to='competition.Sport', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='participant',
            name='tournament',
            field=models.ForeignKey(to='competition.Tournament', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='participant',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='match',
            name='away_team',
            field=models.ForeignKey(related_name='match_away_team', to='competition.Team', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='match',
            name='home_team',
            field=models.ForeignKey(related_name='match_home_team', to='competition.Team', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='match',
            name='tournament',
            field=models.ForeignKey(to='competition.Tournament', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='prediction',
            unique_together=set([('user', 'match')]),
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together=set([('tournament', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='match',
            unique_together=set([('tournament', 'match_id')]),
        ),
    ]
