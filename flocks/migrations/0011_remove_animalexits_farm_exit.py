# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-04 10:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0010_animalflockexit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='animalexits',
            name='farm_exit',
        ),
    ]
