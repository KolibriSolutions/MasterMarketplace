# Generated by Django 2.1.3 on 2019-04-14 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('RecipientsStudents', models.CharField(max_length=400)),
                ('RecipientsStaff', models.CharField(max_length=400)),
                ('Subject', models.CharField(max_length=400)),
                ('Message', models.TextField()),
                ('TimeStamp', models.DateTimeField(auto_now=True, null=True)),
                ('Created', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
    ]
