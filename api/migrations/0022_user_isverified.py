# Generated by Django 3.2.8 on 2021-12-26 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_alter_verificationdocuments_proofofaddress'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='isVerified',
            field=models.BooleanField(default=False, verbose_name='Verification data ok'),
        ),
    ]
