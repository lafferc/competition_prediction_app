# Generated by Django 2.2.26 on 2022-01-28 00:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0004_auto_20220128_0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='benchmark',
            name='prediction_algorithm',
            field=models.IntegerField(choices=[(0, 'Fixed value'), (1, 'Average (mean)'), (3, 'Median'), (2, 'Random range')]),
        ),
    ]