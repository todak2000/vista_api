# Generated by Django 3.2.3 on 2021-07-09 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_escrow_services'),
    ]

    operations = [
        migrations.AddField(
            model_name='services',
            name='details',
            field=models.CharField(max_length=500, null=True, verbose_name='Job/Service Details'),
        ),
        migrations.AddField(
            model_name='services',
            name='tools',
            field=models.CharField(max_length=500, null=True, verbose_name='Tools required for the Job/Service'),
        ),
    ]
