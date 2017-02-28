# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0003_animaldeath_cause'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animaldeath',
            name='weight',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='animalexits',
            name='total_weight',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='flock',
            name='entry_weight',
            field=models.FloatField(),
        ),
    ]
