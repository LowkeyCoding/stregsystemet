# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-09-13 16:20
from __future__ import unicode_literals

from django.db import migrations, models
import kiosk.models


class Migration(migrations.Migration):

    dependencies = [
        ('kiosk', '0002_auto_20170913_1632'),
    ]

    operations = [
        migrations.AddField(
            model_name='kioskitem',
            name='ordering',
            field=models.IntegerField(default=kiosk.models.random_ordering),
        ),
    ]
