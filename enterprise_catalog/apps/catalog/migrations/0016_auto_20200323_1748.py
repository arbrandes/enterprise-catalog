# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-03-23 17:48
from __future__ import unicode_literals

import collections
from django.db import migrations
import jsonfield.encoder
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0015_auto_20200310_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogquery',
            name='content_filter',
            field=jsonfield.fields.JSONField(default=dict, dump_kwargs={'cls': jsonfield.encoder.JSONEncoder, 'separators': (',', ':')}, help_text="Query parameters which will be used to filter the discovery service's search/all endpoint results, specified as a JSON object.", load_kwargs={'object_pairs_hook': collections.OrderedDict}),
        ),
    ]
