from django.shortcuts import render
import datetime
import json
import requests
import jwt
from django.db.models import Q, Sum
from api.models import (User, otp, Transaction, Escrow, Services)
from CustomCode import (autentication, password_functions,
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
        service= request.data.get('service',None)
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
                                password=encryped_password,address=address, state=state, role=role, service=service)
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
                otpData.save()
                return_data = {
                    "success": True,
                    "status" : 200,
                    "role" : user_data.role,
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
def offline(request):
    try:
        email = request.data.get("email",None)

        if not None in email and not '' in email:
            validate_mail = validator.checkmail(email)
            if validate_mail == True:
                if User.objects.filter(email =email).exists() == True:
                    user_data = User.objects.get(email=email)
                    user_data.user_online = False
                    user_data.save()
                    return_data = {
                        "success": True,
                        "status" : 200,
                        "message": "User now offline"
                    }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 202,
            "message": str(e)
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
                    user_data.user_online = True
                    user_data.save()
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
                            "role": f"{user_data.role}",
                        }
                        return Response(return_data)
                    elif is_verified == False:
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
            "success": False,
            "status" : 202,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["GET"])
@autentication.token_required
def dashboard(request,decrypedToken):
    try:
        user_id = decrypedToken['user_id']
        if user_id != None and user_id != '':
            #get user info
            user_data = User.objects.get(user_id=decrypedToken["user_id"])
            userTransactions=Transaction.objects.filter(Q(from_id__icontains=user_id) | Q(to_id__icontains=user_id)).order_by('-date_added')[:20]
            num = len(userTransactions)
            userTransactionsList = []
            for i in range(0,num):
                date_added = userTransactions[i].date_added
                transaction_type  = userTransactions[i].transaction_type
                amount  = userTransactions[i].amount 
                transaction_message = userTransactions[i].transaction_message
                to_json = {
                    "transaction_type": transaction_type,
                    "transaction_message": transaction_message,
                    "amount": amount,
                    "date_added": date_added.strftime('%Y-%m-%d')
                }
                userTransactionsList.append(to_json)
            return_data = {
                "success": True,
                "status" : 200,
                "message": "Successfull",
                "transaction": userTransactionsList,
                "user_details": 
                    {
                        "firstname": f"{user_data.firstname}",
                        "lastname": f"{user_data.lastname}",
                        "email": f"{user_data.email}",
                        "phonenumber": f"{user_data.phone}",
                        "address": f"{user_data.address}",
                        "state": f"{user_data.state}",
                        "role": f"{user_data.role}",
                        "balance": f"{user_data.walletBalance}",
                        "accountname": f"{user_data.account_name}",
                        "accountno": f"{user_data.account_number}",
                        "bank": f"{user_data.bank_name}",
                        "service": f"{user_data.service}",
                    }
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
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["GET"])
@autentication.token_required
def profile(request,decrypedToken):
    try:
        user_id = decrypedToken['user_id']
        if user_id != None and user_id != '':
            #get user info
            user_data = User.objects.get(user_id=decrypedToken["user_id"])
            return_data = {
                "success": True,
                "status" : 200,
                "message": "Successfull",
                "user_details": 
                    {
                        "firstname": f"{user_data.firstname}",
                        "lastname": f"{user_data.lastname}",
                        "email": f"{user_data.email}",
                        "phonenumber": f"{user_data.phone}",
                        "address": f"{user_data.address}",
                        "state": f"{user_data.state}",
                        "role": f"{user_data.role}",
                        "accountname": f"{user_data.account_name}",
                        "accountno": f"{user_data.account_number}",
                        "bank": f"{user_data.bank_name}",
                        "service": f"{user_data.service}",
                        # "isVerified": f"{user_data.address}",
                    }
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
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

# DESIGN AND IMPLEMENT THE JOB PART ASAP***********************
# @api_view(["GET"])
# @autentication.token_required
# def job(request,decrypedToken):
#     try:
#         user_id = decrypedToken['user_id']
#         if user_id != None and user_id != '':
#             #get user info
#             user_data = User.objects.get(user_id=decrypedToken["user_id"])
#             return_data = {
#                 "success": True,
#                 "status" : 200,
#                 "message": "Successfull",
#                 "user_details": 
#                     {
#                         "firstname": f"{user_data.firstname}",
#                         "lastname": f"{user_data.lastname}",
#                         "email": f"{user_data.email}",
#                         "phonenumber": f"{user_data.phone}",
#                         "address": f"{user_data.address}",
#                         "state": f"{user_data.state}",
#                         "role": f"{user_data.role}",
#                         "accountname": f"{user_data.account_name}",
#                         "accountno": f"{user_data.account_number}",
#                         "bank": f"{user_data.bank_name}",
#                         # "isVerified": f"{user_data.address}",
#                     }
#             }
#         else:
#             return_data = {
#                 "success": False,
#                 "status" : 201,
#                 "message": "Invalid Parameter"
#             }
#     except Exception as e:
#         return_data = {
#             "success": False,
#             "status" : 201,
#             "message": str(e)
#         }
#     return Response(return_data)


# EDIT BIO API
@api_view(["PUT"])
def edit_bio(request):
    try:
        user_phone = request.data.get("phone",None)
        new_state = request.data.get("state",None)
        new_address = request.data.get("address",None)
        user_data = User.objects.get(phone=user_phone)  
        
        field = [new_state,new_address]
        if not None in field and not "" in field:
            user_data.address = new_address
            user_data.state = new_state
            user_data.save()
            return_data = {
                "success": True,
                "status" : 200,
                "message": "Bio-Data  Updated Successfully!",
            }
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "message": "One or more fields is Empty!"
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

# UPDATE PASSWORD API
@api_view(["PUT"])
def edit_password(request):
    
    try:
        user_phone = request.data.get("phone",None)
        old_password = request.data.get("old_password",None)
        new_password = request.data.get("new_password",None)
        field = [old_password,new_password]
        user_data = User.objects.get(phone=user_phone)
        if not None in field and not "" in field:
            is_valid_password = password_functions.check_password_match(old_password,user_data.password)
            if is_valid_password == False:
                return_data = {
                    "success": False,
                    "status" : 201,
                    "message": "Old Password is Incorrect"
                }
            else:
                #decrypt password
                encryptpassword = password_functions.generate_password_hash(new_password)
                user_data.password = encryptpassword
                user_data.save()
                return_data = {
                    "success": True,
                    "status" : 200,
                    "message": "Password Changed Successfully! "
                }
    except Exception as e:
        return_data = {
                "success": False,
                "status" : 201,
                "message": str(e)
        }
    return Response(return_data)

# EDIT ACCOUNT API
@api_view(["PUT"])
def edit_account(request):
    try:
        user_phone = request.data.get("phone",None)
        accountName = request.data.get("acc_name",None)
        accountNumber = request.data.get("acc_no",None)
        bankName = request.data.get("bank",None)
        field = [accountName,accountNumber,bankName]
        user_data = User.objects.get(phone=user_phone)
        if not None in field and not "" in field:
            user_data.account_number = accountNumber
            user_data.account_name = accountName
            user_data.bank_name = bankName
            user_data.profile_complete = True
            user_data.save()
            return_data = {
                "success": True,
                "status" : 201,
                "message": "Account saved Successfully!",
            }
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "message": "One or more fields is Empty!"
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

# widthrawal api
@api_view(["POST"])
def withdrawal(request):
    user_phone = request.data.get("phone",None)
    amount = request.POST["amount"]
    account_name = request.data.get("account_name",None) 
    account_no = request.data.get("account_no",None) 
    bank = request.data.get("bank",None) 
    save = request.data.get("save_account_details",None) 
    try: 
        user_data = User.objects.get(phone=user_phone)
        newBalance = user_data.walletBalance - float(amount)
        user_data.walletBalance = newBalance
        if save == "true":
            user_data.account_name = account_name
            user_data.account_number = account_no
            user_data.bank_name = bank
        user_data.save()

        newTransaction = Transaction(from_id=user_data.user_id, to_id="Vista", transaction_type="Debit", transaction_message="Withdrawal - Cashout", amount=float(amount))
        newTransaction.save()
        if user_data and newTransaction:
            # Send mail using SMTP
            mail_subject = user_data.firstname+'! Vista Withdrawal Update'
            email = {
                'subject': mail_subject,
                'html': '<h4>Hello, '+user_data.firstname+'!</h4><p> Your Withdrawal request for NGN'+amount+ ' is being processed and would be sent to your account within 24 hours. Thanks</p>',
                'text': 'Hello, '+user_data.firstname+'!\n Your withdrawal request of NGN'+amount+ ' is being processed and would be sent to your account within 24 hours',
                'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                'to': [
                    {'name': user_data.firstname, 'email': user_data.email}
                ]
            }
            SPApiProxy.smtp_send_mail(email)
            return_data = {
                "success": True,
                "status" : 200,
                "save": save,
                "account_name": user_data.account_name,
                "message": "Withdrawal Successful"
            }
        else:
            return_data = {
            "success": False,
            "status" : 201,
            "message": "something went wrong!"
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["POST"])
def fund(request):
    user_phone = request.data.get("phone",None)
    amount = request.POST["amount"]
    try: 
        user_data = User.objects.get(phone=user_phone)
        newBalance = user_data.walletBalance + float(amount)
        user_data.walletBalance = newBalance
        user_data.save()

        newTransaction = Transaction(from_id="Vista", to_id=user_data.user_id, transaction_type="Credit", transaction_message="Top-up - Paystack", amount=float(amount))
        newTransaction.save()
        if user_data and newTransaction:
            # Send mail using SMTP
            mail_subject = user_data.firstname+'! Vista Top-up Update'
            email = {
                'subject': mail_subject,
                'html': '<h4>Hello, '+user_data.firstname+'!</h4><p> You payment of NGN'+amount+ ' to your Vista wallet was successful</p>',
                'text': 'Hello, '+user_data.firstname+'!\n You payment of NGN'+amount+ ' to your Vista wallet was successful',
                'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                'to': [
                    {'name': user_data.firstname, 'email': user_data.email}
                ]
            }
            SPApiProxy.smtp_send_mail(email)
            return_data = {
                "success": True,
                "status" : 200,
                "message": "Top-Up Successful"
            }
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "message": "something went wrong!"
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["POST"])
def service_request(request):
    user_phone = request.data.get("phone",None)
    service_type = request.data.get("service_type",None)
    service_form= request.data.get("service_form",None)
    address = request.data.get("address",None)
    amount = request.data.get("amount",None)
    payment_mode = request.data.get("payment_mode",None)
    description = request.data.get("description",None)
    try: 
        client_data = User.objects.get(phone=user_phone)
        serviceProviders=User.objects.filter(role='0',state=client_data.state, service=service_type, engaged=False, user_online=True).order_by('-date_added')[:5]
        num = len(serviceProviders)
        serviceProvidersList = []
        for i in range(0,num):
            sp_id = serviceProviders[i].user_id
            sp_firstname = serviceProviders[i].firstname
            sp_lastname = serviceProviders[i].lastname
            date_added = serviceProviders[i].date_added
            sp_address  = serviceProviders[i].address
            sp_phone  = serviceProviders[i].phone 
            sp_state = serviceProviders[i].state
            sp_ratings = serviceProviders[i].ratings
            to_json = {
                "sp_id": sp_id,
                "sp_firstname": sp_firstname,
                "sp_lastname": sp_lastname,
                "sp_address": sp_address,
                "sp_phone": sp_phone,
                "sp_state":sp_state,
                "sp_ratings":sp_ratings,
                "date_added": date_added,
            }
            serviceProvidersList.append(to_json)
        if num > 0:
            newService = Services(client_id=client_data.user_id, amount=amount, service_type=service_type, service_form=service_form, address=address, payment_mode=payment_mode,description=description)
            newService.save()
            return_data = {
                "success": True,
                "status" : 200,
                "job_id": newService.id, 
                "serviceProviders": serviceProvidersList
            }
        if num <= 0:
            return_data = {
                "success": True,
                "status" : 200,
                "message": "Sorry! there are no "+service_type+ " Service Providers around you."
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["POST"])
def accept_sp(request):
    sp_id = request.data.get("sp_id",None)
    job_id = request.data.get("job_id",None)
    try: 
        updateService = Services.objects.get(id=int(job_id))
        updateService.sp_id = sp_id
        updateService.save()

        sp_data = User.objects.get(user_id=sp_id)
        sp_data.engaged =True
        sp_data.save()
        if updateService and sp_data :
            # Send mail using SMTP
            mail_subject = sp_data.firstname+'! Vista Job/Service Update'
            email = {
                'subject': mail_subject,
                'html': '<h4>Hello, '+sp_data.firstname+'!</h4><p> You have a new Job/Service Request from a client. Kindly login to your dashboard and accept/Reject the Job/Service.</p>',
                'text': 'Hello, '+sp_data.firstname+'!\n You have a new Job/Service Request from a client. Kindly login to your dashboard and accept/Reject the Job/Service',
                'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                'to': [
                    {'name': sp_data.firstname, 'email': sp_data.email}
                ]
            }
            SPApiProxy.smtp_send_mail(email)
            return_data = {
                "success": True,
                "status" : 200,
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["GET"])
@autentication.token_required
def services(request,decrypedToken):
    try:
        user_id = decrypedToken['user_id']
        if user_id != None and user_id != '':
            #get user info
            user_data = User.objects.get(user_id=decrypedToken["user_id"])
            if user_data.role == "0":  # artisan
                userServices = Services.objects.filter(sp_id=user_id).order_by('-date_added')[:5]
            else: # client
                userServices = Services.objects.filter(client_id=user_id).order_by('-date_added')[:5]
            
            num = len(userServices)
            userServicesList = []
            for i in range(0,num):
                sp_id = userServices[i].sp_id
                client_id= userServices[i].client_id
                job_id = userServices[i].id
                date_added = userServices[i].date_added
                service_type  = userServices[i].service_type
                isTaken  = userServices[i].isTaken
                isRejectedSP = userServices[i].isRejectedSP
                isCompleted = userServices[i].isCompleted
                to_json = {
                    "sp_id": sp_id,
                    "client_id": client_id,
                    "job_id": job_id,
                    "isTaken": isTaken,
                    "service_type": service_type,
                    "isRejectedSP": isRejectedSP,
                    "isCompleted": isCompleted,
                    "date_added": date_added,
                }
                userServicesList.append(to_json)
            if num > 0:
                return_data = {
                    "success": True,
                    "status" : 200,
                    "message": "Successfull",
                    "user_id": user_data.user_id,
                    "userServices": userServicesList
                }
            if num <= 0:
                return_data = {
                    "success": True,
                    "status" : 200,
                    "message": "Sorry! You have no current job/Service rendered by or for you."
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
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["GET"])
def job_details(request, job_id):
    try:
        # job_id = request.data.get("job_id",None)
        if job_id != None and job_id != '':
            job_data = Services.objects.get(id=job_id)
            client_data = User.objects.get(user_id=job_data.client_id)
            sp_data = User.objects.get(user_id=job_data.sp_id)
            # print(job_data)
            to_json = {
                "sp_id": job_data.sp_id,
                "client_id": job_data.client_id,
                "job_id": job_data.id,
                "details": job_data.details,
                "tools": job_data.tools,
                "budget": job_data.budget,
                "isTaken": job_data.isTaken,
                "sp_phone": sp_data.phone,
                "clientAddress": client_data.address+ " "+client_data.state ,
                "service_type": job_data.service_type,
                "isRejectedSP": job_data.isRejectedSP,
                "isCompleted": job_data.isCompleted,
                "date_added": job_data.date_added,
            }
            
            if job_data:
                return_data = {
                    "success": True,
                    "status" : 200,
                    "message": "Successfull",
                    "job_details": to_json
                }
        else:
            return_data = {
                "success": False,
                "status" : 201,
                "job_id": job_id,
                "message": "Job details don't exist!"
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)


@api_view(["POST"])
def client_cancel(request):
    client_id = request.data.get("client_id",None)
    sp_id = request.data.get("sp_id",None)
    job_id = request.data.get("job_id",None)
    try: 
        updateService = Services.objects.get(id=int(job_id))
        updateService.isRejectedSP = True
        updateService.sp_reject_id = client_id
        updateService.save()

        sp_data = User.objects.get(user_id=sp_id)
        sp_data.engaged =False
        sp_data.save()
        if updateService and sp_data :
            # Send mail using SMTP
            mail_subject = sp_data.firstname+'! Vista Job/Service Update'
            email = {
                'subject': mail_subject,
                'html': '<h4>Hello, '+sp_data.firstname+'!</h4><p> Be kindly informed that the client have canceled the Job.</p>',
                'text': 'Hello, '+sp_data.firstname+'!\n Be kindly informed that the client have canceled the Job.',
                'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                'to': [
                    {'name': sp_data.firstname, 'email': sp_data.email}
                ]
            }
            SPApiProxy.smtp_send_mail(email)
            return_data = {
                "success": True,
                "status" : 200,
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)


@api_view(["POST"])
def client_confirm(request):
    client_id = request.data.get("client_id",None)
    sp_id = request.data.get("sp_id",None)
    job_id = request.data.get("job_id",None)
    ratings = request.data.get("ratings",None)
    try: 
        updateService = Services.objects.get(id=int(job_id))
        updateService.isCompleted = True
        updateService.save()

        sp_data = User.objects.get(user_id=sp_id)
        sp_data.engaged =False
        newRatings = (sp_data.ratings + float(ratings))/2
        sp_data.ratings = newRatings
        fees = (updateService.budget* 0.9)
        newClientBalance = sp_data.walletBalance + fees
        sp_data.walletBalance = newClientBalance
        sp_data.save()
        # updateEscrow=Escrow.objects.get(job_id=job_id)
        # updateEscrow.isPaid = True
        # updateEscrow.save()
        newTransaction = Transaction(from_id="Vista", to_id=sp_data.user_id, transaction_type="Credit", transaction_message="Payment for Job order-"+job_id, amount=float(updateService.budget)* 0.9)
        newTransaction.save()
        if updateService and sp_data  and newTransaction:
            # Send mail using SMTP
            mail_subject = sp_data.firstname+'! Vista Job/Service Update'
            email = {
                'subject': mail_subject,
                'html': '<h4>Hello, '+sp_data.firstname+'!</h4><p> Be kindly informed that the client have confirmed the Job Completion and you have been credited with the sum of NGN'+str(fees)+'. Please kindly check your wallet for your earnings</p>',
                'text': 'Hello, '+sp_data.firstname+'!\n Be kindly informed that the client have confirmed the Job Completion and you have been credited with the sum of NGN'+str(fees)+'. Please kindly check your wallet for your earnings',
                'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                'to': [
                    {'name': sp_data.firstname, 'email': sp_data.email}
                ]
            }
            SPApiProxy.smtp_send_mail(email)
            return_data = {
                "success": True,
                "status" : 200,
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e),
            "fees": fees,
            "newBalance": newClientBalance
        }
    return Response(return_data)

@api_view(["POST"])
def accept_job(request):
    sp_id = request.data.get("sp_id",None)
    job_id = request.data.get("job_id",None)
    try: 
        updateService = Services.objects.get(id=int(job_id))
        updateService.isTaken = True
        updateService.save()
        client_data = User.objects.get(user_id=updateService.client_id)
        commission = float(updateService.budget) * 0.1
        newClientBalance = client_data.walletBalance - float(updateService.budget)
        client_data.walletBalance = newClientBalance
        client_data.save()
        newEscrow=Escrow(job_id=job_id,client_id=client_data.user_id,sp_id=sp_id,budget=updateService.budget, service_type=updateService.service_type,commission=commission)
        newEscrow.save()
        newTransaction = Transaction(from_id=client_data.user_id, to_id="Vista", transaction_type="Debit", transaction_message="Payment for Job order-"+job_id, amount=float(updateService.budget))
        newTransaction.save()
        if updateService and client_data and newEscrow and newTransaction:
            # Send mail using SMTP
            mail_subject = client_data.firstname+'! Vista Job/Service Update'
            email = {
                'subject': mail_subject,
                'html': '<h4>Hello, '+client_data.firstname+'!</h4><p> Your Job/Service offer has been accepted and you have been debited the sum of NGN'+str(updateService.budget)+'. Kindly give the Service provider all the details needed to get the job done. thanks</p>',
                'text': 'Hello, '+client_data.firstname+'!\n Your Job/Service offer has been accepted and you have been debited the sum of NGN'+str(updateService.budget)+'. . Kindly give the Service provider all the details needed to get the job done. thanks',
                'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                'to': [
                    {'name': client_data.firstname, 'email': client_data.email}
                ]
            }
            SPApiProxy.smtp_send_mail(email)
            return_data = {
                "success": True,
                "status" : 200,
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["POST"])
def reject_job(request):
    sp_id = request.data.get("sp_id",None)
    job_id = request.data.get("job_id",None)
    try: 
        updateService = Services.objects.get(id=int(job_id))
        updateService.isRejectedSP = True
        updateService.save()

        sp_data = User.objects.get(user_id=sp_id)
        sp_data.engaged =False
        sp_data.save()
        client_data = User.objects.get(user_id=updateService.client_id)

        newClientBalance = client_data.walletBalance + float(updateService.budget)
        client_data.walletBalance = newClientBalance
        client_data.save()
        newTransaction = Transaction(from_id="Vista", to_id=client_data.user_id, transaction_type="Credit", transaction_message="Refund for Job order-"+job_id, amount=float(updateService.budget))
        newTransaction.save()
        if updateService and sp_data :
            # Send mail using SMTP
            mail_subject = client_data.firstname+'! Vista Job/Service Update'
            email = {
                'subject': mail_subject,
                'html': '<h4>Hello, '+client_data.firstname+'!</h4><p> Your job offer has been humbly turned down by the Service provider and your money has been refunded. Kindly check and search for another provider on the Platform. Thanks</p>',
                'text': 'Hello, '+client_data.firstname+'!\n Your job offer has been humbly turned down by the Service provider and your money has been refunded. Kindly check and search for another provider on the Platform. Thanks',
                'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
                'to': [
                    {'name': client_data.firstname, 'email': client_data.email}
                ]
            }
            SPApiProxy.smtp_send_mail(email)
            return_data = {
                "success": True,
                "status" : 200,
            }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["POST"])
def complete_job(request):
    sp_id = request.data.get("sp_id",None)
    job_id = request.data.get("job_id",None)
    try: 
        updateService = Services.objects.get(id=int(job_id))
       
        client_data = User.objects.get(user_id=updateService.client_id)
        # Send mail using SMTP
        mail_subject = client_data.firstname+'! Vista Job/Service Update'
        email = {
            'subject': mail_subject,
            'html': '<h4>Hello, '+client_data.firstname+'!</h4><p> Your job has been completed by the Service provider. Kindly log on to the Vista app to confirm. Thanks</p>',
            'text': 'Hello, '+client_data.firstname+'!\n Your job has been completed by the Service provider. Kindly log on to the Vista app to confirm. Thanks',
            'from': {'name': 'Vista Fix', 'email': 'donotreply@wastecoin.co'},
            'to': [
                {'name': client_data.firstname, 'email': client_data.email}
            ]
        }
        SPApiProxy.smtp_send_mail(email)
        return_data = {
            "success": True,
            "status" : 200,
        }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)


    # Admin section APis
@api_view(["GET"])
def clients(request):
    try: 
        clients_data = User.objects.filter(role="1")
        num = len(clients_data)
        clientsList = []
        if num > 0:
            for i in range(0,num):
                user_id = clients_data[i].user_id
                name  = clients_data[i].firstname +" "+ clients_data[i].lastname 
                email  = clients_data[i].email 
                phone = clients_data[i].phone
                walletBalance = clients_data[i].walletBalance
                address = clients_data[i].address +" "+ clients_data[i].state

                to_json = {
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "wallet_balance": walletBalance,
                    "address": address
                }
                clientsList.append(to_json)
        else:
            clientsList = ["There are no clients in the database for now!."]
        return_data = {
            "success": True,
            "status" : 200,
            "message": "Successfull",
            "clients": clientsList,
        }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["GET"])
def artisans(request):
    try: 
        artisans_data = User.objects.filter(role="0")
        num = len(artisans_data)
        artisansList = []
        if num > 0:
            for i in range(0,num):
                user_id = artisans_data[i].user_id
                name  = artisans_data[i].firstname +" "+ artisans_data[i].lastname 
                email  = artisans_data[i].email 
                phone = artisans_data[i].phone
                walletBalance = artisans_data[i].walletBalance
                address = artisans_data[i].address +" "+ artisans_data[i].state
                ratings = artisans_data[i].ratings
                account_name = artisans_data[i].account_name
                account_number = artisans_data[i].account_number 
                bank_name = artisans_data[i].bank_name

                to_json = {
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "wallet_balance": walletBalance,
                    "address": address,
                    "ratings":ratings,
                    "account_name": account_name,
                    "account_number": account_number,
                    "bank_name":bank_name
                }
                artisansList.append(to_json)
        else:
            artisansList = ["There are no artisans in the database for now!."]
        return_data = {
            "success": True,
            "status" : 200,
            "message": "Successfull",
            "clients": artisansList,
        }
    except Exception as e:
        return_data = {
            "success": False,
            "status" : 201,
            "message": str(e)
        }
    return Response(return_data)

@api_view(["GET"])
def notification(request, email):
    # email = request.data.get("email",None)

    sp = User.objects.get(email=email)
    if sp.user_online == True and sp.engaged == True:
        check = Services.objects.filter(sp_id=sp.user_id,isTaken=False, isCompleted=False)
        if len(check) == 1:
            return_data = {
            "success": True,
            "status" : 200,
            "sp_online": sp.user_online,
            "sp_engage":sp.engaged,
            "check": len(check),
            "message": "You have a new request"
            }
        else:
            return_data = {
            "success": False,
            "status" : 202,
            "check": len(check),
            "sp_online": sp.user_online,
            "sp_engage":sp.engaged,
            "message": "No Notification"
            }
    else:
        return_data = {
        "success": False,
        "status" : 202,
        "sp_online": sp.user_online,
        "sp_engage":sp.engaged,
        "message": "SP not online"
        }
    return Response(return_data)