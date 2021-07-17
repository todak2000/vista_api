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
    path('api/v1/accept_sp',views.accept_sp),
    path('api/v1/services',views.services),
    path('api/v1/job_details',views.job_details),
]