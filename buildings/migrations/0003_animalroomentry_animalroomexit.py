# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-18 19:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0005_animalseparation'),
        ('buildings', '0002_building_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimalRoomEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('number_of_animals', models.IntegerField()),
                ('flock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flocks.Flock')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buildings.Room')),
            ],
        ),
        migrations.CreateModel(
            name='AnimalRoomExit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('number_of_animals', models.IntegerField()),
                ('flock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flocks.Flock')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buildings.Room')),
            ],
        ),
    ]