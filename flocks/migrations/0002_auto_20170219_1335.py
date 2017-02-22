# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animalexits',
            name='total_weight',
            field=models.DecimalField(max_digits=9, decimal_places=3),
        ),
        migrations.AlterField(
            model_name='flock',
            name='entry_weight',
            field=models.DecimalField(max_digits=9, decimal_places=3),
        ),
    ]
