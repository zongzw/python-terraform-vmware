# Generated by Django 2.0.2 on 2018-02-09 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poc', '0007_auto_20180209_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='virtualmachine',
            name='config',
            field=models.TextField(default='#!/bin/bash\necho "Finished virtual machine provision: `date`"\nuname -a\necho "Starting to configure ..."\n\n# ======= Input your configuration process =======\n\nexit 0\n'),
        ),
        migrations.AlterField(
            model_name='virtualmachine',
            name='status',
            field=models.CharField(default='New', editable=False, max_length=32),
        ),
    ]
