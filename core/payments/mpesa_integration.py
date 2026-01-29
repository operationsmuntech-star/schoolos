"""
M-Pesa Integration Module
Handles M-Pesa payments via STK Push and callbacks.
"""
import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import base64
import hashlib

logger = logging.getLogger(__name__)


class MpesaGateway:
    """M-Pesa payment gateway integration"""
    
    # Sandbox credentials (for development)
    SANDBOX_AUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    SANDBOX_STK_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    SANDBOX_QUERY_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
    
    # Production credentials
    PRODUCTION_AUTH_URL = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    PRODUCTION_STK_URL = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    PRODUCTION_QUERY_URL = "https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query"
    
    def __init__(self):
        """Initialize M-Pesa gateway with settings"""
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', None)
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', None)
        self.business_shortcode = getattr(settings, 'MPESA_SHORTCODE', '174379')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', None)
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', None)
        self.use_production = getattr(settings, 'MPESA_USE_PRODUCTION', False)
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self):
        """Get M-Pesa access token"""
        if self.use_production:
            auth_url = self.PRODUCTION_AUTH_URL
        else:
            auth_url = self.SANDBOX_AUTH_URL
        
        try:
            response = requests.get(
                auth_url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=10
            )
            
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                logger.info("M-Pesa access token obtained")
                return self.access_token
            else:
                logger.error(f"Failed to get M-Pesa token: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting M-Pesa access token: {str(e)}")
            return None
    
    def initiate_stk_push(self, phone_number, amount, account_reference, description):
        """
        Initiate STK push for payment
        
        Args:
            phone_number: Customer phone number (e.g., 254712345678)
            amount: Amount to pay (KES)
            account_reference: Unique reference (e.g., invoice ID)
            description: Payment description
        
        Returns:
            dict with CheckoutRequestID and other response data
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Could not get access token'}
            
            # Normalize phone number
            if not phone_number.startswith('254'):
                phone_number = '254' + phone_number.lstrip('0')
            
            # Prepare timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Generate password (BusinessShortCode + Passkey + Timestamp base64 encoded)
            password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()
            
            # Prepare payload
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": str(account_reference),
                "TransactionDesc": description[:60]  # Limit to 60 chars
            }
            
            # Select URL based on environment
            if self.use_production:
                stk_url = self.PRODUCTION_STK_URL
            else:
                stk_url = self.SANDBOX_STK_URL
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                stk_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                resp_data = response.json()
                logger.info(f"STK push initiated: {resp_data.get('CheckoutRequestID')}")
                return {
                    'success': True,
                    'checkout_request_id': resp_data.get('CheckoutRequestID'),
                    'response_code': resp_data.get('ResponseCode'),
                    'response_description': resp_data.get('ResponseDescription'),
                    'customer_message': resp_data.get('CustomerMessage')
                }
            else:
                logger.error(f"STK push failed: {response.text}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def query_transaction_status(self, checkout_request_id):
        """Query transaction status"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Could not get access token'}
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            if self.use_production:
                query_url = self.PRODUCTION_QUERY_URL
            else:
                query_url = self.SANDBOX_QUERY_URL
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                query_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.text}
        except Exception as e:
            logger.error(f"Error querying transaction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_callback(self, callback_data):
        """
        Process M-Pesa callback from webhook
        
        Args:
            callback_data: JSON data from M-Pesa callback
        
        Returns:
            dict with success status and message
        """
        try:
            # Extract key data from callback
            result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            result_desc = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc', '')
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            merchant_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('MerchantRequestID')
            
            logger.info(f"M-Pesa Callback: CheckoutRequestID={checkout_request_id}, ResultCode={result_code}")
            
            # Result code 0 = Success
            if result_code == 0:
                # Extract callback metadata for transaction details
                callback_metadata = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {})
                item_list = callback_metadata.get('Item', [])
                
                transaction_data = {}
                for item in item_list:
                    name = item.get('Name')
                    value = item.get('Value')
                    transaction_data[name] = value
                
                return {
                    'success': True,
                    'result_code': result_code,
                    'checkout_request_id': checkout_request_id,
                    'merchant_request_id': merchant_request_id,
                    'transaction_data': transaction_data,
                    'message': 'Payment successful'
                }
            else:
                return {
                    'success': False,
                    'result_code': result_code,
                    'message': result_desc or 'Payment failed or was cancelled'
                }
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error processing callback'
            }


def initiate_mpesa_payment(phone_number, amount, invoice_id, description):
    """
    Public function to initiate M-Pesa payment
    
    Args:
        phone_number: Customer phone
        amount: Payment amount
        invoice_id: Invoice ID for reference
        description: Payment description
    
    Returns:
        dict with payment initiation result
    """
    gateway = MpesaGateway()
    return gateway.initiate_stk_push(phone_number, amount, invoice_id, description)


def process_mpesa_callback(callback_data):
    """
    Public function to process M-Pesa webhook callback
    
    Args:
        callback_data: Raw callback JSON from M-Pesa
    
    Returns:
        dict with processing result
    """
    gateway = MpesaGateway()
    return gateway.process_callback(callback_data)
