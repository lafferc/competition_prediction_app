# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0019_benchmark'),
    ]

    operations = [
        migrations.CreateModel(
            name='BenchmarkPrediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('prediction', models.DecimalField(default=0, max_digits=5, decimal_places=2)),
                ('score', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
                ('margin', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
                ('benchmark', models.ForeignKey(to='competition.Benchmark', on_delete=models.CASCADE)),
                ('match', models.ForeignKey(to='competition.Match', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='benchmarkprediction',
            unique_together=set([('benchmark', 'match')]),
        ),
    ]
