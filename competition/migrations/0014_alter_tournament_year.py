# Generated by Django 3.2.19 on 2024-03-03 21:43

import competition.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0013_benchmark_can_receive_bonus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='year',
            field=models.IntegerField(choices=[(2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), (2021, 2021), (2022, 2022), (2023, 2023), (2024, 2024), (2025, 2025)], default=competition.models.current_year),
        ),
    ]
