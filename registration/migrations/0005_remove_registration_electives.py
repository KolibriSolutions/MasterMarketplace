# Generated by Django 2.1.3 on 2019-07-04 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_auto_20190628_1511'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registration',
            name='Electives',
        ),
    ]
