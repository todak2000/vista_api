from django.contrib import admin

from .models import AdminUser, Gallery, PaymentRequest, User, otp, Transaction, Escrow, Services, ServiceCategory, VerificationDocuments

# Register your models here.
admin.site.register(User)
admin.site.register(otp)
admin.site.register(Transaction)
admin.site.register(Escrow)
admin.site.register(Services)
admin.site.register(ServiceCategory) 
admin.site.register(VerificationDocuments) 
admin.site.register(Gallery) 
admin.site.register(AdminUser)
admin.site.register(PaymentRequest)

