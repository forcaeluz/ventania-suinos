# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-07 12:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0006_auto_20170419_1941'),
    ]

    operations = [
        migrations.AddField(
            model_name='animalseparatedfromroom',
            name='destination',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destination_room', to='buildings.Room'),
        ),
        migrations.AlterField(
            model_name='animalseparatedfromroom',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_room', to='buildings.Room'),
        ),
    ]