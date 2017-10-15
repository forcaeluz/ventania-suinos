# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-15 14:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0014_surgeryfromroom_surgery'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimalRoomTransfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buildings.AnimalRoomEntry')),
                ('room_exit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buildings.AnimalRoomExit')),
            ],
        ),
    ]
