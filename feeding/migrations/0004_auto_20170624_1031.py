# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-24 10:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0014_auto_20170604_1048'),
        ('feeding', '0003_auto_20170306_1934'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedingPeriodForFlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('feed_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeding.FeedType')),
                ('flock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flocks.Flock')),
            ],
        ),
        migrations.RemoveField(
            model_name='flockfeedmutation',
            name='feed_type',
        ),
        migrations.RemoveField(
            model_name='flockfeedmutation',
            name='flock',
        ),
        migrations.DeleteModel(
            name='FlockFeedMutation',
        ),
    ]
