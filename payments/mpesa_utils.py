import base64
import json
import requests
import datetime
from datetime import datetime
from django.conf import settings
from requests.auth import HTTPBasicAuth
from .models import MpesaTransaction

def get_access_token():
    """Generate access token for M-Pesa API"""
    consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', 'YOUR_CONSUMER_KEY')
    consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', 'YOUR_CONSUMER_SECRET')
    api_url = getattr(settings, 'MPESA_AUTH_URL', 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials')
    
    try:
        response = requests.get(
            api_url,
            auth=HTTPBasicAuth(consumer_key, consumer_secret)
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        print(f"Error getting access token: {str(e)}")
        return None

def generate_timestamp():
    """Generate timestamp in the format: YYYYMMDDHHMMSS"""
    return datetime.now().strftime('%Y%m%d%H%M%S')

def generate_password(shortcode, passkey, timestamp):
    """Generate password for M-Pesa API"""
    data = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data.encode()).decode()

def stk_push(phone_number, amount, account_reference, description, user=None):
    """Initiate STK push to customer's phone"""
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to get access token"}

    # Get M-Pesa configuration from settings
    business_shortcode = getattr(settings, 'MPESA_PAYBILL', 'YOUR_PAYBILL')
    passkey = getattr(settings, 'MPESA_PASSKEY', 'YOUR_PASSKEY')
    callback_url = getattr(settings, 'MPESA_CALLBACK_URL', 'https://yourdomain.com/mpesa/callback/')
    
    timestamp = generate_timestamp()
    password = generate_password(business_shortcode, passkey, timestamp)
    
    # Format phone number (add country code if not present)
    if not phone_number.startswith('254'):
        if phone_number.startswith('0'):
            phone_number = f"254{phone_number[1:]}"
        else:
            phone_number = f"254{phone_number}"
    
    payload = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": business_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": description
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            getattr(settings, 'MPESA_STK_PUSH_URL', 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'),
            headers=headers,
            json=payload
        )
        response_data = response.json()
        
        # Save transaction to database
        transaction = MpesaTransaction.objects.create(
            user=user,
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=description,
            merchant_request_id=response_data.get('MerchantRequestID'),
            checkout_request_id=response_data.get('CheckoutRequestID'),
            status='pending'
        )
        
        return {
            "success": True,
            "transaction_id": transaction.id,
            "checkout_request_id": transaction.checkout_request_id,
            "merchant_request_id": transaction.merchant_request_id,
            "response": response_data
        }
    except Exception as e:
        return {"error": str(e)}
