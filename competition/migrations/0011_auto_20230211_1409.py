# Generated by Django 3.2.16 on 2023-02-11 14:09

from django.db import migrations, models

# Adds code into UniqueTogether for Team
# To find any teams that fail this constraint run the following sql statement 
# sqlite3 config.db -header "select name,code,sport_id, count(id) from competition_team group by code,sport_id having count(id) > 1;"

class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0010_auto_20230208_0020'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='alt_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='team',
            name='full_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('code', 'sport'), ('alt_name', 'sport'), ('name', 'sport'), ('full_name', 'sport'), ('short_name', 'sport')},
        ),
    ]
