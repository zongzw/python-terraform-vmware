# Generated by Django 2.0.2 on 2018-02-09 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poc', '0005_auto_20180209_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='virtualmachine',
            name='config',
            field=models.TextField(default='#!/bin/bash\nuname -a\necho "Starting to configure ..."\n\n# ======= Input your configuration process =======\n\nexit 0\n'),
        ),
    ]
