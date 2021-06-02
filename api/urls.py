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
    path('api/v1/dashboard',views.change_password),
]