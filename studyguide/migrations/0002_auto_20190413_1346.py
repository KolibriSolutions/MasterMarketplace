# Generated by Django 2.1.3 on 2019-04-13 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studyguide', '0001_squashed_0003_auto_20190413_1219'),
    ]

    operations = [
        migrations.AlterField(
            model_name='masterprogram',
            name='Info',
            field=models.TextField(blank=True, null=True),
        ),
    ]