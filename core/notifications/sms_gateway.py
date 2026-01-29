"""
SMS Provider Gateway - Supports Africa's Talking, Twilio, and Console (development)
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSGateway:
    """Base SMS gateway class"""
    
    @staticmethod
    def send(sms_log):
        """Send SMS via configured provider"""
        provider = getattr(settings, 'SMS_PROVIDER', 'console')
        
        if provider == 'africas-talking':
            return SMSGateway.send_africas_talking(sms_log)
        elif provider == 'twilio':
            return SMSGateway.send_twilio(sms_log)
        else:
            # Default to console for development
            return SMSGateway.send_console(sms_log)
    
    @staticmethod
    def send_console(sms_log):
        """Send SMS to console (development only)
        
        Logs the SMS to logger and marks as sent.
        Useful for testing without real credentials.
        """
        try:
            logger.info(
                f"\n{'='*70}\n"
                f"SMS CONSOLE SEND\n"
                f"{'='*70}\n"
                f"To: {sms_log.phone_number}\n"
                f"Message: {sms_log.message}\n"
                f"Timestamp: {sms_log.created_at}\n"
                f"{'='*70}\n"
            )
            
            return {
                'success': True,
                'message_id': f'console-{sms_log.id}',
                'provider': 'console'
            }
        except Exception as e:
            logger.error(f"Error in console SMS send: {str(e)}")
            return {
                'success': False,
                'error_message': str(e),
                'error_code': 'CONSOLE_ERROR'
            }
    
    @staticmethod
    def send_africas_talking(sms_log):
        """Send via Africa's Talking API
        
        Docs: https://africastalking.com/sms/api
        """
        try:
            import requests
            
            api_key = getattr(settings, 'AFRICAS_TALKING_API_KEY', None)
            username = getattr(settings, 'AFRICAS_TALKING_USERNAME', None)
            
            if not api_key or not username:
                logger.warning("Africa's Talking credentials not configured; falling back to console")
                return SMSGateway.send_console(sms_log)
            
            # Use production URL for live credentials
            url = 'https://api.africastalking.com/version1/messaging'
            
            # Normalize phone number (Kenya example: +254...)
            phone = sms_log.phone_number
            if not phone.startswith('+'):
                # Assume Kenya if starts with 0
                phone = '+254' + phone.lstrip('0') if phone.startswith('0') else '+254' + phone
            
            payload = {
                'username': username,
                'message': sms_log.message,
                'recipients': phone
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                auth=(username, api_key),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                recipients = data.get('SMSMessageData', {}).get('Recipients', [])
                
                if recipients:
                    recipient_data = recipients[0]
                    # Status 101 = queued successfully
                    if recipient_data.get('statusCode') == 101:
                        logger.info(f"Africa's Talking: SMS queued successfully to {phone}")
                        return {
                            'success': True,
                            'message_id': recipient_data.get('messageId', ''),
                            'provider': 'africas-talking'
                        }
                    else:
                        error_msg = recipient_data.get('errorMessage', 'Unknown API error')
                        logger.error(f"Africa's Talking API error: {error_msg}")
                        return {
                            'success': False,
                            'error_message': error_msg,
                            'error_code': str(recipient_data.get('statusCode', 'UNKNOWN'))
                        }
                else:
                    return {
                        'success': False,
                        'error_message': 'No recipients in response',
                        'error_code': 'EMPTY_RECIPIENTS'
                    }
            else:
                logger.error(f"Africa's Talking HTTP error: {response.status_code}")
                return {
                    'success': False,
                    'error_message': f'HTTP {response.status_code}: {response.text}',
                    'error_code': 'HTTP_ERROR'
                }
        except ImportError:
            logger.error("requests library not installed; falling back to console")
            return SMSGateway.send_console(sms_log)
        except Exception as e:
            logger.error(f"Africa's Talking exception: {str(e)}")
            return {
                'success': False,
                'error_message': str(e),
                'error_code': 'EXCEPTION'
            }
    
    @staticmethod
    def send_twilio(sms_log):
        """Send via Twilio API
        
        Docs: https://www.twilio.com/docs/sms/send-messages
        
        Required settings:
            TWILIO_ACCOUNT_SID
            TWILIO_AUTH_TOKEN
            TWILIO_FROM_NUMBER
        """
        try:
            from twilio.rest import Client
            
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
            
            if not all([account_sid, auth_token, from_number]):
                logger.warning("Twilio credentials not configured; falling back to console")
                return SMSGateway.send_console(sms_log)
            
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=sms_log.message,
                from_=from_number,
                to=sms_log.phone_number
            )
            
            logger.info(f"Twilio: SMS sent successfully. SID={message.sid}")
            return {
                'success': True,
                'message_id': message.sid,
                'provider': 'twilio'
            }
        except ImportError:
            logger.error("twilio library not installed; falling back to console")
            return SMSGateway.send_console(sms_log)
        except Exception as e:
            logger.error(f"Twilio exception: {str(e)}")
            return {
                'success': False,
                'error_message': str(e),
                'error_code': 'TWILIO_ERROR'
            }


def send_sms_via_provider(sms_log):
    """Public function to send SMS via configured provider.
    
    Used by Celery tasks and admin actions.
    
    Args:
        sms_log: SMSLog instance
    
    Returns:
        dict: {'success': bool, 'message_id': str, ...}
    """
    return SMSGateway.send(sms_log)
