# orders/utils.py
import hmac
import hashlib
import requests
from django.conf import settings

def initialize_opay_transaction(order, reference, total_amount, callback_url, user_email, user_phone=""):
    """
    Calls OPay Cashier API to initialize a payment session.
    """
    url = settings.OPAY_BASE_URL
    
    # Payload specification for OPay Cashier API
    payload = {
        "merchantId": settings.OPAY_MERCHANT_ID,
        "reference": str(reference),
        "amount": str(int(total_amount)),  # OPay expects total amount string (NGN)
        "currency": "NGN",
        "country": "NG",
        "productName": f"Order #{order.pk} - {order.product_title[:30]}",
        "productDesc": f"Payment for {order.product_title}",
        "userPhone": user_phone or "08000000000",
        "userEmail": user_email,
        "callbackUrl": callback_url,
        "cancelUrl": callback_url,
        "payMethods": ["account", "qrcode", "bankCard", "bankTransfer"],
        "expireAt": "30"  # Expiration in minutes
    }

    # Generate HMAC SHA512 signature using Secret Key
    auth_header = f"Bearer {settings.OPAY_SECRET_KEY}"
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "MerchantId": settings.OPAY_MERCHANT_ID
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        res_data = response.json()
        if res_data.get("code") == "00000":
            return res_data.get("data", {}).get("cashierUrl")  # Returns OPay redirect payment URL
    except Exception as e:
        print(f"OPay Initialization Exception: {e}")
        
    return None