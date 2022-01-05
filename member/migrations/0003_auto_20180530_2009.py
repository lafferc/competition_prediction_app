# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0001_squashed_0027_remove_tournament_late_get_bonus'),
        ('member', '0002_profile_test_features_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token_len', models.PositiveIntegerField(default=6)),
            ],
        ),
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('contact', models.CharField(max_length=50, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(unique=True, max_length=10, blank=True)),
                ('used', models.BooleanField(default=False)),
                ('competition', models.ForeignKey(to='member.Competition')),
            ],
        ),
        migrations.AddField(
            model_name='competition',
            name='organisation',
            field=models.ForeignKey(to='member.Organisation'),
        ),
        migrations.AddField(
            model_name='competition',
            name='participants',
            field=models.ManyToManyField(to='competition.Participant'),
        ),
        migrations.AddField(
            model_name='competition',
            name='tournament',
            field=models.ForeignKey(to='competition.Tournament'),
        ),
        migrations.AlterUniqueTogether(
            name='competition',
            unique_together=set([('tournament', 'organisation')]),
        ),
    ]
