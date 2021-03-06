# Generated by Django 2.0.2 on 2018-02-16 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poc', '0008_auto_20180209_1724'),
    ]

    operations = [
        migrations.RenameField(
            model_name='virtualmachine',
            old_name='num_cpus',
            new_name='cpus',
        ),
        migrations.AddField(
            model_name='virtualmachine',
            name='count',
            field=models.PositiveIntegerField(default='1'),
        ),
        migrations.AlterField(
            model_name='virtualmachine',
            name='log',
            field=models.TextField(default='EOF'),
        ),
        migrations.AlterField(
            model_name='virtualmachine',
            name='status',
            field=models.CharField(default='NEW', max_length=32),
        ),
    ]
