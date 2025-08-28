import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime


def lipa_na_mpesa(phone_number, amount, account_reference="BizHub", transaction_desc="BizHub Payment"):
    """
    Initiates an M-Pesa STK Push request
    """

    # 1. Get access token
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = response.json().get("access_token")

    if not access_token:
        return {"error": "Failed to get access token", "details": response.json()}

    # 2. Generate password
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode("utf-8")

    # 3. STK push request
    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,                # Phone number sending the money
        "PartyB": settings.MPESA_SHORTCODE,    # Paybill number
        "PhoneNumber": phone_number,           # Same as PartyA
        "CallBackURL": settings.MPESA_CALLBACK_URL,  # 👈 pulled from settings.py instead of hardcoding
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    res = requests.post(stk_url, json=payload, headers=headers)

    try:
        return res.json()
    except Exception:
        return {"error": "Invalid JSON response", "details": res.text}
