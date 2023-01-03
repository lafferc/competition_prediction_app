# Generated by Django 3.2.16 on 2023-01-03 19:07

import competition.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0008_auto_20221231_1351'),
    ]

    operations = [
        migrations.AddField(
            model_name='sport',
            name='extra_time_name',
            field=models.CharField(default='extra time', max_length=50),
        ),
        migrations.AddField(
            model_name='sport',
            name='knockout_decider_name',
            field=models.CharField(blank=True, default='penalty shootout', max_length=50),
        ),
        migrations.AlterField(
            model_name='tournament',
            name='year',
            field=models.IntegerField(choices=[(2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), (2021, 2021), (2022, 2022), (2023, 2023), (2024, 2024)], default=competition.models.current_year),
        ),
    ]
