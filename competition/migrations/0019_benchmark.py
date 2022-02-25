# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0018_auto_20190217_2313'),
    ]

    operations = [
        migrations.CreateModel(
            name='Benchmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True)),
                ('margin_per_match', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
                ('name', models.CharField(max_length=50)),
                ('prediction_algorithm', models.IntegerField(choices=[(0, b'Fixed value'), (1, b'Average'), (2, b'Random range')])),
                ('static_value', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
                ('range_start', models.IntegerField(null=True, blank=True)),
                ('range_end', models.IntegerField(null=True, blank=True)),
                ('tournament', models.ForeignKey(to='competition.Tournament', on_delete=models.CASCADE)),
            ],
        ),
    ]
