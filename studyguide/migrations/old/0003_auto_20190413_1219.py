# Generated by Django 2.1.3 on 2019-04-13 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studyguide', '0002_auto_20190218_1534'),
    ]

    operations = [
        migrations.AlterField(
            model_name='capacitygroup',
            name='Info',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='masterprogram',
            name='Info',
            field=models.TextField(blank=True, null=True),
        ),
    ]
