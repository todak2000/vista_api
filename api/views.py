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
                        # {'name': firstName, 'email': "todak2000@gmail.com"}
                        {'name': firstName, 'email': email}
                    ]
                }
                sentMail = SPApiProxy.smtp_send_mail(email)
                if new_userData and user_OTP and sentMail:
                    return_data = {
                        "success": True,
                        "status" : 200,
                        "message": "The registration was successful.",
                        "user_id": userRandomId,
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
def verify(request):
    try:
        code = request.data.get('code',None)
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
                    "status" : 200,
                    "message": "Your Account is now Validated!"
                }
                return Response(return_data)
            else:
                return_data = {
                    "success": False,
                    "status" : 201,
                    "message": "Wrong Code Entered. Try again!"
                }
                return Response(return_data)
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "message": "Kindly enter the codes sent to your email"
            }
            return Response(return_data)
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
        }
    return Response(return_data)

# RESEND VERIFICATION CODE API
@api_view(["POST"])
def resend_code(request):
    try:
        user_id= request.data.get('user_id',None)
        field = [user_id]
        if not None in field and not "" in field:
            if User.objects.filter(user_id =user_id).exists():
                getOtp = otp.objects.get(user__user_id = user_id)

                userData = User.objects.get(user_id = user_id)
                firstName = userData.firstname
                code = getOtp.otp_code
                if code:
                    # Resend mail using SMTP
                    mail_subject = 'Activate Code Sent again for your Vista account.'
                    resentEmail = {
                        'subject': mail_subject,
                        'html': '<h4>Hello, '+firstName+'!</h4><p>Kindly find the Verification Code below sent again to activate your Vista Account</p> <h1>'+code+'</h1>',
                        'text': 'Hello, '+firstName+'!\nKindly find the Verification Code below sent againto activate your Vista Account',
                        'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                        'to': [
                            {'name': firstName, 'email': userData.email}
                        ]
                    }
                    SPApiProxy.smtp_send_mail(resentEmail)
                    return_data = {
                        "success": True,
                        "status" : 200,
                        "message": "Verfication Code sent again!"
                    }
                    return Response(return_data)
                else:
                    return_data = {
                        "success": False,
                        "status" : 202,
                        "message": "We could not retrieve your Verification Code. Kindly register!"
                    }
                    return Response(return_data)
        else:
            return_data = {
                "success": False,
                "status" : 202,
                "message": "An error occured. Try again later"
            }
            return Response(return_data)
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
            # "message": "Something went wrong!"
        }
    return Response(return_data)

# SEND PASSWORD LINK (FOROGT PASSWORD PAGE) API
@api_view(["POST"])
def forgot_password(request):
    try:
        email = request.data.get('email',None)
        field = [email]
        if not None in field and not "" in field:
            if User.objects.filter(email =email).exists():
                
                getOtp = otp.objects.get(user__email = email)
                userData = User.objects.get(email = email)
                firstName = userData.firstname
                #Generate reset OTP
                resetCode = string_generator.numeric(4)
                #Save reset OTP
                getOtp.password_reset_code=resetCode
                getOtp.save()

                if getOtp:
                    # Resend mail using SMTP
                    mail_subject = 'Reset your Vista account Password Confirmation.'
                    resentEmail = {
                        'subject': mail_subject,
                        'html': '<h4>Hi, '+firstName+'!</h4><p>Kindly find the Reset Code below to confirm that intend to change your Vista Account Password</p> <h1>'+getOtp.password_reset_code+'</h1>',
                        'text': 'Hello, '+firstName+'!\nKindly find the Reset Code below to confirm that intend to change your Vista Account Password',
                        'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                        'to': [
                            {'name': firstName, 'email': email}
                        ]
                    }
                    SPApiProxy.smtp_send_mail(resentEmail)
                    return_data = {
                        "success": True,
                        "status" : 200,
                        "user_id": userData.user_id,
                        "message": "Reset Code sent!"
                    }
                    return Response(return_data)
                else:
                    return_data = {
                        "success": False,
                        "status" : 202,
                        "message": "Sorry! try again"
                    }
                    return Response(return_data)
            elif validator.checkmail(email) == False:
                return_data = {
                    "success": False,
                    "status" : 202,
                    "message": "Email is Invalid"
                }
                return Response(return_data)
            else:
                return_data = {
                    "success": False,
                    "status" : 202,
                    "message": "Email does not exist in our database"
                }
                return Response(return_data)
        else:
            return_data = {
                "success": False,
                "status" : 202,
                "message": "One or more fields is empty!"
            }
            return Response(return_data)
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
            # "message": "Something went wrong!"
        }
    return Response(return_data)

# CONFIRM USER FOR PASSWORD CHANGE
@api_view(["POST"])
def confirm_user_password(request):
    try:
        code = request.data.get('code',None)
        user_id = request.data.get('user_id',None)
        field = [user_id, code]
        if not None in field and not "" in field:
            getOtp = otp.objects.get(password_reset_code=code)
            if getOtp.user.user_id == user_id:
                return_data = {
                    "success": True,
                    "status" : 200,
                    "user_id": user_id,
                    "message": "User Confirmed!"
                }
                return Response(return_data)
            else:
                return_data = {
                    "success": False,
                    "status" : 202,
                    "message": "Sorry! try again"
                }
                return Response(return_data)
        else:
            return_data = {
                "success": False,
                "status" : 202,
                "message": "One or more fields is empty!"
            }
            return Response(return_data)
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
            # "message": "Something went wrong!"
        }
    return Response(return_data)


# CHANGE PASSWORD API
@api_view(["POST"])
def change_password(request):
    try:
        user_id = request.data.get("user_id",None)
        new_password = request.data.get("password",None)
        confirm_new_password = request.data.get("confirm_password",None)
        user_data = User.objects.get(user_id=user_id)  
        
        if user_data:
            if new_password != confirm_new_password:
                return_data = {
                    "success": False,
                    "status" : 202,
                    "message": "Password do not match!"
                }
                return Response(return_data)
            else:
                encryptpassword = password_functions.generate_password_hash(new_password)
                user_data.user_password = encryptpassword
                user_data.save()
                return_data = {
                    "success": True,
                    "status" : 200,
                    "message": "Password Changed Successfully! Kindly login"
                }
                return Response(return_data)
        else:
            return_data = {
                "success": False,
                "status" : 202,
                "message": 'Sorry, You are not Authorized to access this link!'
            }
            return Response(return_data)
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
            # "message": 'Sorry, Something went wrong!'
        }
    return Response(return_data)

#SIGNIN API
@api_view(["POST"])
def signin(request):
    try:
        email = request.data.get("email",None)
        password = request.data.get("password",None)
        field = [email,password]
        if not None in field and not '' in field:
            validate_mail = validator.checkmail(email)
            if validate_mail == True:
                if User.objects.filter(email =email).exists() == False:
                    return_data = {
                        "success": False,
                        "status" : 202,
                        "message": "User does not exist"
                    }
                else:
                    user_data = User.objects.get(email=email)
                    is_valid_password = password_functions.check_password_match(password,user_data.password)
                    is_verified = otp.objects.get(user__phone=user_data.phone).validated
                    #Generate token
                    timeLimit= datetime.datetime.utcnow() + datetime.timedelta(minutes=1440) #set limit for user
                    payload = {"user_id": f'{user_data.user_id}',
                               "validated": is_verified,
                               "exp":timeLimit}
                    token = jwt.encode(payload,settings.SECRET_KEY)
                    if is_valid_password and is_verified:
                        return_data = {
                            "success": True,
                            "status" : 200,
                            "message": "Successfull",
                            "token": token.decode('UTF-8'),
                            "token-expiration": f"{timeLimit}",
                            "user_id": user_data.user_id,
                            "user_details": 
                                {
                                    "firstname": f"{user_data.firstname}",
                                    "lastname": f"{user_data.lastname}",
                                    "email": f"{user_data.email}",
                                    "phonenumber": f"{user_data.user_phone}",
                                    "address": f"{user_data.user_address}"
                                }
                        }
                        return Response(return_data)
                    elif is_verified == False:
                        getOtp = otp.objects.get(user_data__user_id = user_data.user_id)
                        code = getOtp.otp_code
                        # Resend mail using SMTP
                        mail_subject = 'Activate Code Sent again for your Vista account.'
                        resentEmail = {
                            'subject': mail_subject,
                            'html': '<h4>Hello, '+user_data.firstname+'!</h4><p>Kindly find the Verification Code below sent again to activate your Vista Account</p> <h1>'+code+'</h1>',
                            'text': 'Hello, '+user_data.firstname+'!\nKindly find the Verification Code below sent againto activate your Vista Account',
                            'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                            'to': [
                                {'name': user_data.firstname, 'email': user_data.email}
                            ]
                        }
                        SPApiProxy.smtp_send_mail(resentEmail)
                        return_data = {
                            "success": False,
                            "user_id": user_data.user_id,
                            "message": "User is not verified",
                            "status" : 205,
                            "token": token.decode('UTF-8')
                        }
                        return Response(return_data)
                    else:
                        return_data = {
                            "success": False,
                            "status" : 201,
                            "message" : "Wrong Password"
                        }
                        return Response(return_data)
            else:
                return_data = {
                    "success": False,
                    "status" : 201,
                    "message": "Email is Invalid"
                }
                return Response(return_data)
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "message" : "Invalid Parameters"
            }
            return Response(return_data)
    except Exception as e:
        return_data = {
            "success": True,
            "status" : 200,
            "message": str(e)
        }
    return Response(return_data)
