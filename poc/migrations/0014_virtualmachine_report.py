# Generated by Django 2.0.2 on 2018-02-20 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poc', '0013_auto_20180219_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtualmachine',
            name='report',
            field=models.TextField(default='None'),
        ),
    ]