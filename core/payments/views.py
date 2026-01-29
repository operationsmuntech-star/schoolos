from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from core.users.models import Student
from core.fees.models import Invoice, FeePayment
from core.attendance.models import Attendance
from core.examinations.models import Marks
from core.notifications.models import Notification
from .mpesa_integration import initiate_mpesa_payment, process_mpesa_callback
from datetime import datetime, timedelta

def index(request):
    return render(request, 'payments/index.html')

@login_required
def parent_portal(request):
    """
    Parent portal view - displays student fee, payment, attendance, exam data
    """
    return render(request, 'parent/portal.html')


@login_required
def initiate_payment(request):
    """
    Initiate M-Pesa payment for an invoice
    POST params: invoice_id, phone_number
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        invoice_id = data.get('invoice_id')
        phone_number = data.get('phone_number')
        
        # Verify invoice exists and belongs to current user's child
        invoice = Invoice.objects.get(id=invoice_id)
        # You may want to add permission check here
        
        # Initiate M-Pesa payment
        result = initiate_mpesa_payment(
            phone_number=phone_number,
            amount=float(invoice.total_amount),
            invoice_id=invoice.id,
            description=f"{invoice.description} - Invoice {invoice.id}"
        )
        
        return JsonResponse(result)
    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """
    M-Pesa webhook callback handler
    Receives payment confirmation from M-Pesa
    """
    try:
        callback_data = json.loads(request.body)
        
        # Process callback
        result = process_mpesa_callback(callback_data)
        
        if result.get('success'):
            # Extract transaction data
            transaction_data = result.get('transaction_data', {})
            merchant_request_id = result.get('merchant_request_id')
            checkout_request_id = result.get('checkout_request_id')
            
            # Get transaction reference/code
            mpesa_receipt = transaction_data.get('MpesaReceiptNumber')
            mpesa_amount = transaction_data.get('Amount')
            
            # Try to find and update the corresponding FeePayment
            # The invoice ID should be in the account reference from original request
            # For now, we log the successful payment
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"M-Pesa payment received: Receipt={mpesa_receipt}, Amount={mpesa_amount}")

            # Attempt to map to a FeePayment by checkout_request_id or account reference
            # If AccountReference present in transaction_data, use it as invoice id
            account_ref = transaction_data.get('AccountReference') or transaction_data.get('Account')
            payment_updated = False
            if account_ref:
                # account_ref might be invoice id
                try:
                    invoice_id = int(account_ref)
                    payments = FeePayment.objects.filter(invoice__id=invoice_id, payment_method='mpesa')
                    for p in payments:
                        p.mpesa_transaction_id = mpesa_receipt
                        p.mpesa_callback_json = callback_data
                        p.status = 'completed'
                        p.save()
                        payment_updated = True
                except Exception:
                    # Not an integer invoice id; skip
                    pass

            # Fallback: try matching by reference fields
            if not payment_updated and mpesa_receipt:
                payments = FeePayment.objects.filter(reference__icontains=mpesa_receipt)
                for p in payments:
                    p.mpesa_transaction_id = mpesa_receipt
                    p.mpesa_callback_json = callback_data
                    p.status = 'completed'
                    p.save()
                    payment_updated = True

            if not payment_updated:
                logger.warning('Could not match M-Pesa callback to a FeePayment; logged raw callback')
            
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Accepted'
            })
        else:
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': result.get('message', 'Payment processing failed')
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Error processing callback'
        })
