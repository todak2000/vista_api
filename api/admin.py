from django.contrib import admin

from .models import User, otp, AccountDetails

# Register your models here.
admin.site.register(User)
admin.site.register(otp)
admin.site.register(AccountDetails)
