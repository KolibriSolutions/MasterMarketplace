# Generated by Django 2.1.5 on 2019-02-18 14:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registrationtracking',
            name='Blob',
        ),
    ]
