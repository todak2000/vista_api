# Generated by Django 3.2.3 on 2021-05-30 22:04

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=500, unique=True)),
                ('firstname', models.CharField(blank=True, max_length=30, verbose_name='Firstname')),
                ('lastname', models.CharField(blank=True, max_length=30, verbose_name='Lastname')),
                ('email', models.EmailField(max_length=90, unique=True, verbose_name='Email')),
                ('phone', models.CharField(max_length=15, null=True, unique=True, verbose_name='Telephone number')),
                ('password', models.TextField(max_length=200, verbose_name='Password')),
                ('address', models.TextField(max_length=200, null=True, verbose_name='Address')),
                ('state', models.TextField(max_length=200, null=True, verbose_name='State')),
                ('ratings', models.FloatField(default=1.0, max_length=200, verbose_name='Job Ratings')),
                ('role', models.TextField(default='client', max_length=50, verbose_name='User role')),
                ('walletBalance', models.FloatField(default=0.0, verbose_name='Balance')),
                ('account_name', models.TextField(default='Null', max_length=150, verbose_name='Account Name')),
                ('account_number', models.TextField(default='0000000000', max_length=150, verbose_name='Account Number')),
                ('bank_name', models.TextField(default='Null', max_length=150, verbose_name='Bank Name')),
                ('profile_complete', models.BooleanField(default=False)),
                ('terms_conditions', models.BooleanField(default=False)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'Vista_user_table',
            },
        ),
        migrations.CreateModel(
            name='otp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_code', models.TextField(max_length=20, verbose_name='OTP CODE')),
                ('validated', models.BooleanField(default=False)),
                ('password_reset_code', models.TextField(default='', max_length=20, verbose_name='Reset Code')),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.user')),
            ],
            options={
                'db_table': 'OTP_Code',
            },
        ),
        migrations.CreateModel(
            name='AccountDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_name', models.TextField(max_length=150, unique=True, verbose_name='Account Name')),
                ('account_number', models.TextField(max_length=150, unique=True, verbose_name='Account Number')),
                ('bank_name', models.TextField(max_length=150, verbose_name='Bank Name')),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.user')),
            ],
            options={
                'db_table': 'Account Details',
            },
        ),
    ]
