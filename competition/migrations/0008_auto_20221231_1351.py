# Generated by Django 3.2.16 on 2022-12-31 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0007_auto_20220302_0107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='benchmarkprediction',
            name='correct',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='prediction',
            name='correct',
            field=models.BooleanField(null=True),
        ),
    ]
