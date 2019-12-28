# Generated by Django 2.1.5 on 2019-02-16 10:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import tracking.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationTracking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Timestamp', models.DateTimeField(auto_now_add=True)),
                ('Type', models.CharField(choices=[('a', 'applied'), ('r', 'retracted')], max_length=1)),
                ('Project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applicationtrackings', to='projects.Project')),
                ('Student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applicationtrackings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DistributionTracking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Timestamp', models.DateTimeField(auto_now_add=True)),
                ('Type', models.CharField(choices=[('d', 'distributed'), ('u', 'undistributed')], max_length=1)),
                ('Project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distributiontrackings', to='projects.Project')),
                ('Student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distributiontrackings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ProjectStatusChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Timestamp', models.DateTimeField(auto_now_add=True)),
                ('StatusFrom', models.CharField(choices=[(1, 'Draft, awaiting completion by assistant'), (2, 'Draft, awaiting approval by responsible staff'), (3, 'Active project')], max_length=16)),
                ('StatusTo', models.CharField(choices=[(1, 'Draft, awaiting completion by assistant'), (2, 'Draft, awaiting approval by responsible staff'), (3, 'Active project')], max_length=16)),
                ('Message', models.CharField(blank=True, max_length=500, null=True)),
                ('Actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='StatusChangeTracking', to=settings.AUTH_USER_MODEL)),
                ('Subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='StatusChangeTracking', to='projects.Project')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectTracking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tracking', to='projects.Project')),
                ('UniqueVisitors', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationTracking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TimeStamp', models.DateTimeField(auto_now_add=True)),
                ('Blob', models.TextField()),
                ('Student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrationtrackings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TelemetryKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Created', models.DateTimeField(auto_now_add=True)),
                ('ValidUntil', models.DateField(blank=True, null=True)),
                ('Key', models.CharField(default=tracking.models.generate_key, max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserLogin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Timestamp', models.DateTimeField(auto_now_add=True)),
                ('Twofactor', models.BooleanField(default=False)),
                ('Subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logins', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
