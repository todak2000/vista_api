from django.contrib import admin

from .models import User, otp, Transaction, Escrow, Services, ServiceCategory

# Register your models here.
admin.site.register(User)
admin.site.register(otp)
admin.site.register(Transaction)
admin.site.register(Escrow)
admin.site.register(Services)
admin.site.register(ServiceCategory) 

