# Generated by Django 2.1.5 on 2019-02-16 10:39

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import markdownx.models
import timeline.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accesscontrol', '0001_initial'),
        ('timeline', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CapacityGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ShortName', models.CharField(max_length=3)),
                ('FullName', models.CharField(max_length=256)),
                ('Info', markdownx.models.MarkdownxField(blank=True, default='', help_text='Limited mark down is supported. You can style [links](http://master.ele.tue.nl/), **bold** and _italics_')),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Code', models.CharField(max_length=32)),
                ('Name', models.CharField(max_length=256)),
                ('Quartile', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('Timeslot', models.CharField(max_length=1)),
                ('Responsiblestaff', models.CharField(max_length=256)),
                ('StaffEmail', models.EmailField(blank=True, max_length=254, null=True)),
                ('DetailLink', models.URLField()),
                ('Type', models.IntegerField(choices=[(1, 'Course'), (2, 'Administration')], default=1, help_text='If the course is a normal course or a code for administration')),
                ('Group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='studyguide.CapacityGroup')),
                ('TargetAudience', models.ManyToManyField(related_name='target_courses', to='accesscontrol.Origin')),
                ('Year', models.ForeignKey(default=timeline.utils.get_year_id, on_delete=django.db.models.deletion.CASCADE, to='timeline.Year')),
            ],
            options={
                'ordering': ['Quartile'],
            },
        ),
        migrations.CreateModel(
            name='GroupAdministratorThrough',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Super', models.BooleanField(blank=True, default=False)),
                ('Group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studyguide.CapacityGroup')),
                ('User', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='administratoredgroups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MasterProgram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=32)),
                ('DetailLink', models.URLField(blank=True, null=True)),
                ('Info', markdownx.models.MarkdownxField(blank=True, help_text='Limited mark down is supported. You can style [links](http://master.ele.tue.nl/), **bold** and _italics_', null=True)),
                ('Courses', models.ManyToManyField(blank=True, related_name='programs', to='studyguide.Course')),
                ('Group', models.ManyToManyField(related_name='programs', to='studyguide.CapacityGroup')),
                ('Year', models.ForeignKey(default=timeline.utils.get_year_id, on_delete=django.db.models.deletion.CASCADE, to='timeline.Year')),
            ],
        ),
        migrations.CreateModel(
            name='MenuLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.TextField(max_length=32)),
                ('Url', models.URLField()),
                ('Icon', models.TextField(blank=True, help_text='For instance "files-empty" or "heart" ', max_length=32, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='capacitygroup',
            name='Administrators',
            field=models.ManyToManyField(related_name='administratorgroups', through='studyguide.GroupAdministratorThrough', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='capacitygroup',
            name='Head',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='capacity_group_head', to=settings.AUTH_USER_MODEL),
        ),
    ]
