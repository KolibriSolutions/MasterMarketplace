# Generated by Django 2.1.3 on 2019-07-01 13:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accesscontrol', '0005_accessgrantstaff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allowedaccess',
            name='Origin',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='students', to='accesscontrol.Origin'),
        ),
    ]
