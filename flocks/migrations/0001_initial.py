# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnimalDeath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('weight', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AnimalExits',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('total_weight', models.DecimalField(max_digits=5, decimal_places=3)),
                ('number_of_animals', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Flock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entry_date', models.DateField()),
                ('entry_weight', models.DecimalField(max_digits=5, decimal_places=3)),
                ('number_of_animals', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='animalexits',
            name='flock',
            field=models.ForeignKey(to='flocks.Flock'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='animaldeath',
            name='flock',
            field=models.ForeignKey(to='flocks.Flock'),
            preserve_default=True,
        ),
    ]
