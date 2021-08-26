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
    user_online = models.BooleanField(default=False)
    service= models.TextField(max_length=150,verbose_name="Service Rendered",null=True)
    engaged = models.BooleanField(default=False, verbose_name="Is the SP currently doing a job")
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user_id} - {self.user_online} - {self.service} - {self.engaged} {self.email} - {self.address}- {self.state}"

class otp(models.Model):
    class Meta:
        db_table = "OTP_Code"
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.TextField(max_length=20,verbose_name="OTP CODE")
    validated = models.BooleanField(default=False)
    password_reset_code = models.TextField(max_length=20,verbose_name="Reset Code",default="")
    date_added = models.DateTimeField(default=timezone.now)

class Transaction(models.Model):
    class Meta:
        db_table = "Transaction Table"
    # Transactions
    from_id = models.TextField(max_length=20,verbose_name="Sending Party",null=True)
    to_id = models.TextField(max_length=20,verbose_name="Recieving Party",null=True)
    transaction_type = models.TextField(max_length=20,verbose_name="Type of Transaction",null=True)
    transaction_message= models.TextField(max_length=500,verbose_name="Message", null=True)
    amount = models.FloatField(verbose_name="Amount Sent",null=True)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.from_id} - {self.to_id} - {self.transaction_type} - {self.amount}"

class Escrow(models.Model):
    class Meta:
        db_table = "Escrow_table"
    # Escrow 
    job_id = models.TextField(max_length=20,verbose_name="Job ID",null=True)
    client_id = models.TextField(max_length=20,verbose_name="Client ID",null=True)
    sp_id = models.TextField(max_length=20,verbose_name="Service Provider ID",null=True)
    budget= models.FloatField(max_length=500,verbose_name="Client Budget", null=True)
    service_type= models.TextField(max_length=500,verbose_name="Type of Services/Job", null=True)
    commission = models.CharField(default=0,max_length=500, verbose_name="Vista's Commission",null=True)
    payment_mode= models.CharField(max_length=500,verbose_name="Payment Mode", null=True)
    dispute = models.BooleanField(default=False, verbose_name="Did Client raise dispute")
    isPaid = models.BooleanField(default=False, verbose_name="Was payment made to Service Provider")
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.client_id} - {self.sp_id}  - {self.job_id} - {self.dispute} - {self.isPaid} - {self.payment_mode}"

class Services(models.Model):
    class Meta:
        db_table = "Services_table"
    # Services
    client_id = models.TextField(max_length=20,verbose_name="Client ID",null=True)
    sp_id = models.TextField(max_length=20,verbose_name="Service Provider ID",null=True)
    amount= models.FloatField(max_length=500,verbose_name="Service Charge", null=True)
    service_type= models.TextField(max_length=500,verbose_name="Type of Services/Job", null=True)
    sp_reject_id= models.TextField(max_length=500,verbose_name="Service Provider ID who rejected job", null=True)
    
    service_form= models.CharField(max_length=500,verbose_name="Service Type/form", null=True)
    address= models.CharField(max_length=500,verbose_name="Address", null=True)
    payment_mode= models.CharField(max_length=500,verbose_name="Payment Mode", null=True)
    description= models.CharField(max_length=10500,verbose_name="Description", null=True)
    specific_service = models.CharField(max_length=500,verbose_name="Exact Service", null=True)
    unit= models.CharField(max_length=500,verbose_name="Quantity/Unit per Service", null=True)
    isTaken = models.BooleanField(default=False, verbose_name="is the Job taken by an SP")
    isRejectedSP = models.BooleanField(default=False, verbose_name="Did the first SP rejected the Job")
    isCompleted = models.BooleanField(default=False, verbose_name="Did SP finish the Job")
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.client_id} - {self.sp_id} - {self.amount} - {self.service_type} {self.isTaken} - {self.isRejectedSP}"

class ServiceCategory(models.Model):
    class Meta:
        db_table = "Service Category and Pricing"
    # Service Category and Pricing
    service= models.TextField(max_length=500,verbose_name="Service", null=True)
    type = models.CharField(max_length=500,verbose_name="Type of Services", null=True)
    amount = models.FloatField(verbose_name="Price/Unit Service",null=True)

    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.service} - {self.type} - {self.amount} "