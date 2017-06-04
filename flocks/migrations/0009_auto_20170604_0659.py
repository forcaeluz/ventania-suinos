# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-04 06:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0008_auto_20170603_1750'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimalFarmExit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_weight', models.FloatField()),
                ('number_of_animals', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='animalexits',
            name='farm_exit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='flocks.AnimalFarmExit'),
        ),
    ]
