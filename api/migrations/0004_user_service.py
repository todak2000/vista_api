# Generated by Django 3.2.3 on 2021-07-09 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20210610_1405'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='service',
            field=models.TextField(max_length=150, null=True, verbose_name='Service Rendered'),
        ),
    ]
