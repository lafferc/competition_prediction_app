# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings

def init_profiles(apps, schema_editor):
    Profile = apps.get_model("member", "Profile")
    User = apps.get_model("auth", "User")

    for user in User.objects.all():
        Profile.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dob', models.DateField(null=True, blank=True)),
                ('display_name_format', models.IntegerField(default=0, help_text=b'This how other users will see you name displayed', choices=[(0, b'Full Name'), (1, b'username'), (2, b'user_id')])),
                ('can_receive_emails', models.BooleanField(default=True, help_text=b'Global email setting, if false the user will not receive any emails')),
                ('email_on_new_competition', models.BooleanField(default=True, help_text=b'User will receive an email when new competitions are started')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.RunPython(init_profiles, migrations.RunPython.noop),
    ]
