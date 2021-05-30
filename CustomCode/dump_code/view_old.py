from django.shortcuts import render
import datetime
import jwt
# from api.models import (AccountDetails, AgentCoins, AgentTransactionHistory,
#                         ContactUs, User, UserCoins, UserTrasactionHistory, otp)
# from CustomCode import (autentication, fixed_var, password_functions, sms,
#                         string_generator, validator)
from apis.models import (User, otp)
from CustomCode import (autentication, fixed_var, password_functions, sms,
                        string_generator, validator)
from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response
from agrilance import settings
# Create your views here.

@api_view(['GET'])
def index_page(request):
    return_data = {
        "error" : "0",
        "status" : 200,
        "message" : "Successful"
    }
    return Response(return_data)

# SIGN UP API
@api_view(["POST"])
def signup(request):
    try:
        firstName = request.data.get('firstname',None)
        lastName = request.data.get('lastname',None)
        phoneNumber = request.data.get('phonenumber',None)
        email = request.data.get('email',None)
        password = request.data.get('password',None)
        address = request.data.get('address',None)
        reg_field = [firstName,lastName,phoneNumber,email,password,address]
        if not None in reg_field and not "" in reg_field:
            if User.objects.filter(user_phone =phoneNumber).exists() or User.objects.filter(email =email).exists():
                return_data = {
                    "error": "1",
                    "message": "User Exists"
                }
            elif validator.checkmail(email) == False or validator.checkphone(phoneNumber)== False:
                return_data = {
                    "error": "1",
                    "message": "Email or Phone number is Invalid"
                }
            else:
                #generate user_id
                userRandomId = string_generator.alphanumeric(6)
                #encrypt password
                encryped_password = password_functions.generate_password_hash(password)
                #Save user_data
                new_userData = User(user_id=userRandomId,firstname=firstName,lastname=lastName,
                                email=email,user_phone=phoneNumber,
                                user_password=encryped_password,user_address=address)
                new_userData.save()
                #Generate OTP
                code = string_generator.numeric(6)
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
                message = f"Welcome to Agrilance, your verification code is {code}"
                sms.sendsms(phoneNumber[1:],message)
                return_data = {
                    "error": "0",
                    "message": "The registration was successful, A verification SMS has been sent",
                    "token": f"{token.decode('UTF-8')}",
                    "elapsed_time": f"{timeLimit}",
                    }
        else:
            return_data = {
                "error":"2",
                "message": "Invalid Parameter"
            }
    except Exception as e:
        return_data = {
            "error": "3",
            "message": str(e)
        }
    return Response(return_data)

#VERIFICATION API
@api_view(["POST"])
@autentication.token_required
def verification(request,decrypedToken):
    try:
        otp_entered = request.data.get("otp",None)
        if otp_entered != None and otp_entered != "":
            user_data = otp.objects.get(user__user_id=decrypedToken['user_id'])
            otpCode,date_added = user_data.otp_code,user_data.date_added
            date_now = datetime.datetime.now(datetime.timezone.utc)
            duration = float((date_now - date_added).total_seconds())
            timeLimit = 1800.0 #30 mins interval
            if otp_entered == otpCode and duration < timeLimit:
                #validate user
                user_data.validated = True
                user_data.save()
                return_data = {
                    "error": "0",
                    "message":"User Verified"
                }
            elif otp_entered != otpCode and duration < timeLimit:
                return_data = {
                    "error": "1",
                    "message": "Incorrect OTP"
                }
            elif otp_entered == otpCode and duration > timeLimit:
                return_data = {
                    "error": "1",
                    "message": "OTP has expired"
                }
        else:
            return_data = {
                "error": "2",
                "message": "Invalid Parameters"
            }
    except Exception:
        return_data = {
            "error": "3",
            "message": "An error occured"
        }
    return Response(return_data)


#RESEND OTP
@api_view(["POST"])
def resend_otp(request):
    try:
        phone_number = request.data.get('phonenumber',None)
        if phone_number != None and phone_number != "":
            if User.objects.filter(user_phone =phone_number).exists() == False:
                    return_data = {
                        "error": "1",
                        "message": "User does not exist"
                    }
            else:
                user_data = otp.objects.get(user__user_phone=phone_number)
                user = User.objects.get(user_phone=phone_number)
                #generate new otp
                code = string_generator.numeric(6)
                user_data.otp_code = code
                user_data.save()
                message = f"Welcome to Agrilance, your new verification code is {code}"
                sms.sendsms(phone_number[1:],message)
                timeLimit= datetime.datetime.utcnow() + datetime.timedelta(minutes=1440) #set limit for user
                payload = {"user_id": f'{user.user_id}',
                           "validated": user_data.validated,
                           "exp":timeLimit}
                token = jwt.encode(payload,settings.SECRET_KEY)
                return_data = {
                    "error": "0",
                    "message": "OTP has been sent to your phone number",
                    "token": token.decode('UTF-8')
                }
        else:
            return_data = {
                "error": "2",
                "message": "Invalid Parameters"
            }
    except Exception as e:
        return_data = {
            "error": "3",
            "message": str(e)
        }
    return Response(return_data)


#User login
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
                        "error": "1",
                        "message": "User does not exist"
                    }
                else:
                    user_data = User.objects.get(email=email)
                    is_valid_password = password_functions.check_password_match(password,user_data.user_password)
                    is_verified = otp.objects.get(user__user_phone=user_data.user_phone).validated
                    #Generate token
                    timeLimit= datetime.datetime.utcnow() + datetime.timedelta(minutes=1440) #set limit for user
                    payload = {"user_id": f'{user_data.user_id}',
                               "validated": is_verified,
                               "exp":timeLimit}
                    token = jwt.encode(payload,settings.SECRET_KEY)
                    if is_valid_password and is_verified:
                        return_data = {
                            "error": "0",
                            "message": "Successfull",
                            "token": token.decode('UTF-8'),
                            "token-expiration": f"{timeLimit}",
                            "user_details": [
                                {
                                    "firstname": f"{user_data.firstname}",
                                    "lastname": f"{user_data.lastname}",
                                    "email": f"{user_data.email}",
                                    "phonenumber": f"{user_data.user_phone}",
                                    "address": f"{user_data.user_address}"
                                }
                            ]

                        }
                    elif is_verified == False:
                        return_data = {
                            "error" : "1",
                            "message": "User is not verified",
                            "token": token.decode('UTF-8')
                        }
                    else:
                        return_data = {
                            "error" : "1",
                            "message" : "Wrong Password"
                        }
            else:
                return_data = {
                    "error": "2",
                    "message": "Email is Invalid"
                }
        else:
            return_data = {
                "error" : "2",
                "message" : "Invalid Parameters"
                }
    except Exception as e:
        return_data = {
            "error": "3",
            "message": str(e)
        }
    return Response(return_data)


@api_view(["POST"])
def reset_password(request):
    try:
        phone_number = request.data.get('phonenumber',None)
        if phone_number != None and phone_number != "":
            if User.objects.filter(user_phone =phone_number).exists() == False:
                return_data = {
                    "error": "1",
                    "message": "User does not exist"
                }
            else:
                user_data = otp.objects.get(user__user_phone=phone_number)
                user = User.objects.get(user_phone=phone_number)
                generate_pin = string_generator.alphanumeric(6)
                user_data.password_reset_code = generate_pin
                user_data.save()
                message = f"Welcome to Agrilance, your password reset code is {generate_pin}"
                sms.sendsms(phone_number[1:],message)
                timeLimit= datetime.datetime.utcnow() + datetime.timedelta(minutes=1440) #set limit for user
                payload = {"user_id": f'{user.user_id}',
                           "validated": user_data.validated,
                           "exp":timeLimit}
                token = jwt.encode(payload,settings.SECRET_KEY)
                return_data = {
                    "error": "0",
                    "message": "Successful, reset code sent to Phone Number",
                    "token": token.decode('UTF-8')
                }
        else:
            return_data = {
                "error": "2",
                "message": "Invalid Parameter"
            }
    except Exception as e:
        return_data = {
            "error": "3",
            "message": str(e)
        }
    return Response(return_data)

#VERIFICATION PASSOWRDAPI
@api_view(["POST"])
@autentication.token_required
def verification_password(request,decrypedToken):
# def verification_password(request):
    try:
        reset_code = request.data.get("reset_code",None)
        # user_id = request.data.get("user_id",None)
        if reset_code != None and reset_code != "":
            user_data = otp.objects.get(user__user_id=decrypedToken['user_id'])
            # user_data = otp.objects.get(user__user_id=user_id)
            dbResetCode,date_added = user_data.password_reset_code,user_data.date_added
            date_now = datetime.datetime.now(datetime.timezone.utc)
            duration = float((date_now - date_added).total_seconds())
            timeLimit = 1800.0 #30 mins interval

            if reset_code == dbResetCode and duration < timeLimit:
                user_data.save()
                payload = {"user_id": f'{user_data.user.user_id}',
                           "validated": user_data.validated,
                           "reset_code": reset_code,
                           "exp":timeLimit}
                token = jwt.encode(payload,settings.SECRET_KEY)
                return_data = {
                    "error": "0",
                    "message":"User permitted to change password, redirect to change password page",
                    "token": token.decode('UTF-8')
                }
            elif reset_code != dbResetCode and duration < timeLimit:
                return_data = {
                    "error": "1",
                    "message": "Incorrect Reset Password Code"
                }
            elif reset_code == dbResetCode and duration > timeLimit:
                return_data = {
                    "error": "1",
                    "message": "Reset Password Code has expired"
                }
        else:
            return_data = {
                "error": "2",
                "message": "Invalid Parameters"
            }
    except Exception as e:
        return_data = {
            "error": "3",
            "message": str(e)
        }
    return Response(return_data)

#Change password
@api_view(["POST"])
@autentication.token_required
def password_change(request,decrypedToken):
# def password_change(request):
    try:
        # reset_code = decrypedToken['reset_code'])
        reset_code = request.data.get("reset_code",None)
        new_password = request.data.get("new_password",None)
        fields = [reset_code,new_password]
        if not None in fields and not "" in fields:
            #get user info
            user_data = User.objects.get(user_id=decrypedToken["user_id"])
            otp_reset_code = otp.objects.get(user__user_id=decrypedToken["user_id"]).password_reset_code
            # print(otp_reset_code)
            if reset_code == otp_reset_code:
                #encrypt password
                encryptpassword = password_functions.generate_password_hash(new_password)
                user_data.user_password = encryptpassword
                user_data.save()
                return_data = {
                    "error": "0",
                    "message": "Successfull, Password Changed",
                    "token": token.decode('UTF-8')
                }
            elif reset_code != otp_reset_code:
                return_data = {
                    "error": "1",
                    "message": "Code does not Match"
                }
        else:
            return_data = {
                "error": "2",
                "message": "Invalid Parameters"
            }
    except Exception:
        return_data = {
            "error": "3",
            "message": "An error occured"
        }
    return Response(return_data)
