# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import competition.models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0009_auto_20170506_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='year',
            field=models.IntegerField(default=competition.models.current_year, choices=[(2000, 2000), (2001, 2001), (2002, 2002), (2003, 2003), (2004, 2004), (2005, 2005), (2006, 2006), (2007, 2007), (2008, 2008), (2009, 2009), (2010, 2010), (2011, 2011), (2012, 2012), (2013, 2013), (2014, 2014), (2015, 2015), (2016, 2016), (2017, 2017)]),
        ),
    ]
