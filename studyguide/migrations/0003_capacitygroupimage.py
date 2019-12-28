# Generated by Django 2.1.3 on 2019-05-25 07:44

from django.db import migrations, models
import django.db.models.deletion
import studyguide.models


class Migration(migrations.Migration):

    dependencies = [
        ('studyguide', '0002_auto_20190413_1346'),
    ]

    operations = [
        migrations.CreateModel(
            name='CapacityGroupImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('File', models.ImageField(default=None, upload_to=studyguide.models.CapacityGroupImage.make_upload_path)),
                ('Caption', models.CharField(blank=True, max_length=200, null=True)),
                ('OriginalName', models.CharField(blank=True, max_length=200, null=True)),
                ('CapacityGroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='studyguide.CapacityGroup')),
            ],
        ),
    ]
