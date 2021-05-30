from django.urls import path

from . import views

urlpatterns = [
    path('',views.index),                                              #tested
    path('api/v1/signup',views.signup), 
    path('api/v1/verify',views.verify), 
    path('api/v1/resend_code',views.resend_code), 
]