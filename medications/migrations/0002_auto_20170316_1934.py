# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-16 19:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medication',
            name='name',
            field=models.CharField(max_length=140, unique=True),
        ),
    ]
