# Generated by Django 2.1.3 on 2019-03-19 17:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accesscontrol', '0002_auto_20190216_1139'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='allowedaccess',
            name='Type',
        ),
    ]
