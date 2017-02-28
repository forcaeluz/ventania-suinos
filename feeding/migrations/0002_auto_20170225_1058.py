# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0003_animaldeath_cause'),
        ('feeding', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlockFeedMutation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('feed_type', models.ForeignKey(to='feeding.FeedType', null=True)),
                ('flock', models.ForeignKey(to='flocks.Flock')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RenameField(
            model_name='feedtype',
            old_name='start_feeding_at',
            new_name='start_feeding_age',
        ),
        migrations.RenameField(
            model_name='feedtype',
            old_name='stop_feeding_at',
            new_name='stop_feeding_age',
        ),
        migrations.AlterField(
            model_name='feedtype',
            name='name',
            field=models.CharField(unique=True, max_length=20),
        ),
    ]
