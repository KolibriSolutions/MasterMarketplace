# Generated by Django 2.1.3 on 2019-05-25 10:32

from django.db import migrations, models
import django.db.models.deletion
import studyguide.models


class Migration(migrations.Migration):

    dependencies = [
        ('studyguide', '0003_capacitygroupimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='MasterProgramImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('File', models.ImageField(default=None, upload_to=studyguide.models.MasterProgramImage.make_upload_path)),
                ('Caption', models.CharField(blank=True, max_length=200, null=True)),
                ('OriginalName', models.CharField(blank=True, max_length=200, null=True)),
                ('MasterProgram', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='studyguide.MasterProgram')),
            ],
        ),
    ]
