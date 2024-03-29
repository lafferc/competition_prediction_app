# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-05-27 21:59
from __future__ import unicode_literals

from django.db import migrations, models

def update_predictions(apps, schema_editor):
    Prediction = apps.get_model("competition", "Prediction")
    BenchmarkPrediction = apps.get_model("competition", "BenchmarkPrediction")
    # Match = apps.get_model("competition", "Match")

    def is_correct(p):
        if p.match.score is None:
            return None
        if p.prediction == p.match.score:
            return True
        if p.prediction < 0 and p.match.score < 0:
            return True
        if p.prediction > 0 and p.match.score > 0:
            return True
        return False

    for p in Prediction.objects.all():
        p.correct = is_correct(p)
        p.save()

    for p in BenchmarkPrediction.objects.all():
        p.correct = is_correct(p)
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0025_auto_20210525_2305'),
    ]

    operations = [
        migrations.AddField(
            model_name='benchmarkprediction',
            name='correct',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='prediction',
            name='correct',
            field=models.NullBooleanField(),
        ),
        migrations.RunPython(update_predictions, migrations.RunPython.noop),
    ]
