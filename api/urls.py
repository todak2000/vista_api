from django.urls import path

from . import views

urlpatterns = [
    path('',views.index),                                              #tested
    path('api/v1/signup',views.signup), 
    path('api/v1/signin',views.signin),
    path('api/v1/verify',views.verify), 
    path('api/v1/resend_code',views.resend_code), 
    path('api/v1/forgot_password',views.forgot_password),
    path('api/v1/confirm_user_password',views.confirm_user_password),
    path('api/v1/change_password',views.change_password),
    path('api/v1/dashboard',views.dashboard),
    path('api/v1/profile',views.profile),

    path('api/v1/edit_bio',views.edit_bio),
    path('api/v1/edit_account',views.edit_account),
    path('api/v1/edit_password',views.edit_password),
    path('api/v1/withdrawal',views.withdrawal),
    path('api/v1/fund',views.fund),

    # v2 apis starts here
    path('api/v1/request',views.service_request),
    path('api/v1/accept_sp',views.accept_sp), # client accepting sp
    path('api/v1/services',views.services),
    path('api/v1/job_details/<int:job_id>',views.job_details),
    path('api/v1/client_cancel',views.client_cancel),
    path('api/v1/client_confirm',views.client_confirm),

    path('api/v1/accept_job',views.accept_job), 
    path('api/v1/reject_job',views.reject_job), 
    path('api/v1/complete_job',views.complete_job), 
    path('api/v1/cash_collected/<job_id>',views.cash_collected), 

    # Admin
    path('api/v1/clients',views.clients), 
    path('api/v1/artisans',views.artisans), 
    path('api/v1/notification/<email>',views.notification),
    path('api/v1/service_list/<service_type>',views.service_list),
    path('api/v1/deactivate_user',views.deactivate_user), 
    path('api/v1/activate_user',views.activate_user),
    path('api/v1/add_new_service',views.add_service_category), 
]