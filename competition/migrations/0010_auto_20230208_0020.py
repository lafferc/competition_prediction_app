# Generated by Django 3.2.16 on 2023-02-08 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0009_alter_tournament_year'),
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
        migrations.AddField(
            model_name='team',
            name='short_name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('name', 'sport'), ('short_name', 'sport'), ('code', 'sport')},
        ),
    ]
