from django.db import models
from django.utils import timezone
# Create your models here.
class User(models.Model):
    class Meta:
        db_table = "Vista_user_table"
    user_id = models.CharField(max_length=500,unique=True)
    firstname = models.CharField(max_length=30,verbose_name="Firstname",blank=True)
    lastname = models.CharField(max_length=30,verbose_name="Lastname",blank=True)
    email = models.EmailField(max_length=90, unique=True,verbose_name="Email")
    phone = models.CharField(max_length=15, unique=True, null=True, verbose_name="Telephone number")
    password = models.TextField(max_length=200,verbose_name="Password")
    address = models.TextField(max_length=200,verbose_name="Address", null=True)
    state = models.TextField(max_length=200,verbose_name="State", null=True)
    ratings = models.FloatField(max_length=200,verbose_name="Job Ratings", default=1.0)
    role = models.TextField(max_length=50,verbose_name="User role",default="client")
    walletBalance = models.FloatField(verbose_name="Balance",default=0.00)
    # account details
    account_name = models.TextField(max_length=150,verbose_name="Account Name",default="Account Name")
    account_number = models.TextField(max_length=150,verbose_name="Account Number",default="Account Number")
    bank_name = models.TextField(max_length=150,verbose_name="Bank Name",default="Bank")

    # compliance with vista's terms and condition
    profile_complete = models.BooleanField(default=False)
    terms_conditions = models.BooleanField(default=False)

    date_added = models.DateTimeField(default=timezone.now)

class AccountDetails(models.Model):
    class Meta:
        db_table = "Account Details"
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    account_name = models.TextField(max_length=150,unique=True,verbose_name="Account Name")
    account_number = models.TextField(max_length=150,unique=True,verbose_name="Account Number")
    bank_name = models.TextField(max_length=150,verbose_name="Bank Name")
    date_added = models.DateTimeField(default=timezone.now)

class otp(models.Model):
    class Meta:
        db_table = "OTP_Code"
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.TextField(max_length=20,verbose_name="OTP CODE")
    validated = models.BooleanField(default=False)
    password_reset_code = models.TextField(max_length=20,verbose_name="Reset Code",default="")
    date_added = models.DateTimeField(default=timezone.now)
