# Generated by Django 2.1.3 on 2019-07-01 13:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('studyguide', '0005_auto_20190628_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='capacitygroup',
            name='Head',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='capacity_group_head', to=settings.AUTH_USER_MODEL),
        ),
    ]
