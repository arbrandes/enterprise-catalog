# Generated by Django 3.2.8 on 2021-12-09 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0027_auto_20211125_0559'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogupdatecommandconfig',
            name='no_async',
            field=models.BooleanField(default=False, help_text="If true, for management commands that respect this field, celery tasks will not be apply_async()'d, but instead exectue as regular python functions."),
        ),
    ]