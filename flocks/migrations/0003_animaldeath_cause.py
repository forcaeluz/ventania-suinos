# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0002_auto_20170219_1335'),
    ]

    operations = [
        migrations.AddField(
            model_name='animaldeath',
            name='cause',
            field=models.TextField(default='Unknown'),
            preserve_default=False,
        ),
    ]
