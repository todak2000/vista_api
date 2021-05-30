from django.shortcuts import render
import datetime
import json
import requests
import jwt
from django.db.models import Q
from api.models import (User, otp, AccountDetails)
from CustomCode import (autentication, fixed_var, password_functions,
                        string_generator, validator)
# from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response
from vista import settings

from pysendpulse.pysendpulse import PySendPulse
from decouple import config

REST_API_ID = config("REST_API_ID")
REST_API_SECRET = config("REST_API_SECRET")
TOKEN_STORAGE = config("TOKEN_STORAGE")
MEMCACHED_HOST = config("MEMCACHED_HOST")
SPApiProxy = PySendPulse(REST_API_ID, REST_API_SECRET, TOKEN_STORAGE, memcached_host=MEMCACHED_HOST)

@api_view(['GET'])
def index(request):
    return_data = {
        "success": True,
        "status" : 200,
        "message" : "Successful"
    }
    return Response(return_data)

# SIGN UP API
@api_view(["POST"])
def signup(request):
    try:
        firstName = request.data.get('firstName',None)
        lastName = request.data.get('lastName',None)
        phoneNumber = request.data.get('phoneNumber',None)
        email = request.data.get('email',None)
        password = request.data.get('password',None)
        address = request.data.get('address',None)
        state = request.data.get('state',None)
        role= request.data.get('role',None)
        reg_field = [firstName,lastName,phoneNumber,email,password,address, state, role]
        if not None in reg_field and not "" in reg_field:
            if User.objects.filter(phone =phoneNumber).exists() or User.objects.filter(email =email).exists():
                return_data = {
                    "success": False,
                    "status" : 201,
                    "message": "User Exists"
                }
            elif validator.checkmail(email) == False or validator.checkphone(phoneNumber)== False:
                return_data = {
                    "success": False,
                    "status" : 201,
                    "message": "Email or Phone number is Invalid"
                }
            else:
                #generate user_id
                if role == 0:
                    userRandomId = "SP"+string_generator.numeric(4)
                else:
                    userRandomId = "CT"+string_generator.numeric(4)
                #encrypt password
                encryped_password = password_functions.generate_password_hash(password)
                #Save user_data
                new_userData = User(user_id=userRandomId,firstname=firstName,lastname=lastName,
                                email=email,phone=phoneNumber,
                                password=encryped_password,address=address, state=state, role=role)
                new_userData.save()
                #Generate OTP
                code = string_generator.numeric(4)
                #Save OTP
                user_OTP =otp(user=new_userData,otp_code=code)
                user_OTP.save()

                # Get User Validation
                validated = otp.objects.get(user__user_id=userRandomId).validated
                #Generate token
                timeLimit= datetime.datetime.utcnow() + datetime.timedelta(minutes=1440) #set duration for token
                payload = {"user_id": f"{userRandomId}",
                           "validated": validated,
                           "exp":timeLimit}
                token = jwt.encode(payload,settings.SECRET_KEY)
                # Send mail using SMTP
                mail_subject = 'Activate your Vista account.'
                email = {
                    'subject': mail_subject,
                    'html': '<h4>Hello, '+firstName+'!</h4><p>Kindly use the Verification Code below to activate your Vista Account</p> <h1>'+code+'</h1>',
                    'text': 'Hello, '+firstName+'!\nKindly use the Verification Code below to activate your Vista Account',
                    'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                    'to': [
                        {'name': firstName, 'email': "todak2000@gmail.com"}
                        # {'name': firstName, 'email': email}
                    ]
                }
                sentMail = SPApiProxy.smtp_send_mail(email)
                if new_userData and user_OTP and sentMail:
                    return_data = {
                        "success": True,
                        "status" : 200,
                        "user_id": userRandomId,
                        "message": "The registration was successful.",
                        "token": f"{token.decode('UTF-8')}",
                        "elapsed_time": f"{timeLimit}",
                        }
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "message": "Invalid Parameter"
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["POST"])
# @autentication.token_required
def verify(request):
    try:
        code = request.data.get('code',None)
        # user_id = decrypedToken['user_id']
        user_id = request.data.get('user_id',None)

        reg_field = [user_id, code]
        if not None in reg_field and not "" in reg_field:
            #get user info
            user_data = User.objects.get(user_id=user_id)
            otpData = otp.objects.get(user=user_data)
            if otpData.otp_code == code:
                otpData.validated = True
                return_data = {
                    "success": True,
                    "status" : 201,
                    "message": "Your Account is now Validated!"
                }
            
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "message": "Invalid Parameter"
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
        }
    return Response(return_data)
