# Generated by Django 2.0.2 on 2018-02-16 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poc', '0009_auto_20180216_1349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='virtualmachine',
            name='status',
            field=models.CharField(choices=[('NEW', 'NEW'), ('CREATING', 'CREATING'), ('CREATED', 'CREATED'), ('PROVISIONING', 'PROVISIONING'), ('READY', 'READY'), ('TODEL', 'TODEL'), ('DESTROYING', 'DESTROYING'), ('DELETED', 'DELETED')], default='NEW', max_length=32),
        ),
    ]