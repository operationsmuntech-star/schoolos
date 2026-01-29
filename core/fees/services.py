from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging
import re

from .models import (
    Term, FeeStructure, StudentFeeOverride, Invoice,
    FeePayment, PaymentReceipt, Arrears, MpesaTransaction
)
from core.users.models import Student, School

logger = logging.getLogger(__name__)


class InvoiceGenerationService:
    """Service for generating invoices from fee structures"""

    @staticmethod
    def generate_invoices_for_term(term, school=None, class_assigned=None, user=None):
        """
        Generate invoices for students based on fee structures

        Args:
            term: Term instance
            school: School instance (if None, use all schools with fee structures)
            class_assigned: StudentClass instance (if None, generate for all applicable)
            user: User instance for audit trail

        Returns:
            dict with 'created' count, 'skipped' count, and 'errors' list
        """
        results = {
            'created': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            # Get fee structures
            fee_structures = FeeStructure.objects.filter(term=term)
            if school:
                fee_structures = fee_structures.filter(school=school)
            if class_assigned:
                fee_structures = fee_structures.filter(
                    models.Q(class_assigned=class_assigned) | models.Q(class_assigned__isnull=True)
                )

            with transaction.atomic():
                for fee_structure in fee_structures:
                    try:
                        # Get students to invoice
                        students = Student.objects.filter(
                            school=fee_structure.school,
                            is_active=True
                        )

                        if fee_structure.class_assigned:
                            students = students.filter(
                                student_class=fee_structure.class_assigned
                            )

                        for student in students:
                            # Check if invoice already exists
                            existing = Invoice.objects.filter(
                                student=student,
                                term=term
                            ).exists()

                            if existing:
                                results['skipped'] += 1
                                continue

                            # Calculate amount (considering overrides)
                            amount = fee_structure.amount
                            override = StudentFeeOverride.objects.filter(
                                student=student,
                                term=term,
                                fee_structure=fee_structure
                            ).first()

                            if override:
                                if override.override_amount is None:  # Waived
                                    amount = Decimal('0')
                                else:
                                    amount = override.override_amount

                            # Create invoice
                            invoice = Invoice.objects.create(
                                student=student,
                                term=term,
                                total_amount=amount,
                                amount_paid=Decimal('0'),
                                status='issued',
                                created_by=user
                            )
                            results['created'] += 1

                    except Exception as e:
                        logger.error(f"Error creating invoices for fee structure {fee_structure.id}: {str(e)}")
                        results['errors'].append({
                            'fee_structure_id': fee_structure.id,
                            'error': str(e)
                        })

        except Exception as e:
            logger.error(f"Error in generate_invoices_for_term: {str(e)}")
            results['errors'].append({
                'general_error': str(e)
            })

        return results


class PaymentService:
    """Service for processing payments"""

    @staticmethod
    def record_payment(invoice, amount, payment_method, reference='', user=None):
        """
        Record a payment for an invoice

        Args:
            invoice: Invoice instance
            amount: Decimal amount
            payment_method: str ('mpesa', 'bank', 'cash', 'check')
            reference: str payment reference/transaction ID
            user: User instance for audit trail

        Returns:
            Payment instance

        Raises:
            ValidationError if payment invalid
        """
        if amount <= 0:
            raise ValidationError("Payment amount must be greater than 0")

        if amount > invoice.balance:
            raise ValidationError(
                f"Payment amount {amount} exceeds invoice balance {invoice.balance}"
            )

        try:
            with transaction.atomic():
                payment = FeePayment.objects.create(
                    invoice=invoice,
                    amount=amount,
                    payment_method=payment_method,
                    reference=reference,
                    status='completed',
                    recorded_by=user
                )

                # Update invoice balance
                invoice.amount_paid = invoice.amount_paid + amount
                invoice.balance = invoice.total_amount - invoice.amount_paid

                # Update invoice status
                if invoice.balance == 0:
                    invoice.status = 'paid'
                elif invoice.balance < invoice.total_amount:
                    invoice.status = 'partial'

                invoice.save()

                # Update or create arrears record
                try:
                    arrears = Arrears.objects.get(
                        student=invoice.student,
                        school=invoice.student.school
                    )
                    if invoice.balance == 0:
                        arrears.is_resolved = True
                        arrears.resolved_date = timezone.now()
                    arrears.save()
                except Arrears.DoesNotExist:
                    pass

                logger.info(f"Payment recorded: {payment.id} for invoice {invoice.id}")
                return payment

        except IntegrityError as e:
            logger.error(f"Integrity error recording payment: {str(e)}")
            raise ValidationError("Error recording payment")
        except Exception as e:
            logger.error(f"Error in record_payment: {str(e)}")
            raise


class ArrearsService:
    """Service for managing arrears"""

    @staticmethod
    def update_arrears_for_student(student):
        """
        Update arrears status for a student

        Args:
            student: Student instance

        Returns:
            dict with 'created' and 'updated' counts
        """
        results = {'created': 0, 'updated': 0}

        try:
            # Get all overdue invoices
            overdue_invoices = Invoice.objects.filter(
                student=student,
                balance__gt=0,
                status__in=['issued', 'partial', 'overdue'],
                due_date__lt=timezone.now().date()
            )

            if overdue_invoices.exists():
                total_arrears = sum(inv.balance for inv in overdue_invoices)
                oldest_invoice = overdue_invoices.order_by('due_date').first()
                days_outstanding = (timezone.now().date() - oldest_invoice.due_date).days

                try:
                    arrears = Arrears.objects.get(
                        student=student,
                        school=student.school
                    )
                    arrears.total_arrears = total_arrears
                    arrears.days_outstanding = days_outstanding
                    arrears.is_resolved = False
                    arrears.save()
                    results['updated'] += 1
                except Arrears.DoesNotExist:
                    Arrears.objects.create(
                        student=student,
                        school=student.school,
                        total_arrears=total_arrears,
                        days_outstanding=days_outstanding,
                        is_resolved=False
                    )
                    results['created'] += 1

                # Mark invoices as overdue
                overdue_invoices.filter(status='issued').update(status='overdue')
                overdue_invoices.filter(status='partial').update(status='overdue')

            else:
                # No overdue invoices, mark as resolved
                try:
                    arrears = Arrears.objects.get(
                        student=student,
                        school=student.school
                    )
                    if not arrears.is_resolved:
                        arrears.is_resolved = True
                        arrears.resolved_date = timezone.now()
                        arrears.save()
                        results['updated'] += 1
                except Arrears.DoesNotExist:
                    pass

        except Exception as e:
            logger.error(f"Error in update_arrears_for_student: {str(e)}")

        return results

    @staticmethod
    def update_all_arrears():
        """
        Update arrears for all students (typically run as Celery task)

        Returns:
            dict with total 'created' and 'updated' counts
        """
        results = {'created': 0, 'updated': 0}

        try:
            # Get all students with invoices
            students = Student.objects.filter(
                invoice__isnull=False
            ).distinct()

            for student in students:
                res = ArrearsService.update_arrears_for_student(student)
                results['created'] += res['created']
                results['updated'] += res['updated']

        except Exception as e:
            logger.error(f"Error in update_all_arrears: {str(e)}")

        return results


class MpesaService:
    """Service for M-Pesa payment integration"""

    @staticmethod
    def find_matching_invoice(amount, phone_number):
        """
        Find invoice matching M-Pesa payment

        Args:
            amount: Decimal amount
            phone_number: str phone number

        Returns:
            Invoice instance or None
        """
        # Normalize phone number (remove + and country code if present)
        phone = phone_number.lstrip('+')
        if phone.startswith('254'):
            phone = phone[3:]  # Remove country code
        # Add 0 prefix for Kenyan format
        if not phone.startswith('0'):
            phone = '0' + phone

        try:
            # Search for student by phone number
            from core.users.models import CustomUser
            user = CustomUser.objects.filter(phone__icontains=phone).first()

            if user and hasattr(user, 'student'):
                student = user.student
                # Find matching invoice
                invoice = Invoice.objects.filter(
                    student=student,
                    balance=amount,
                    status__in=['issued', 'partial', 'overdue']
                ).first()

                if invoice:
                    return invoice

                # If no exact match, try to find closest amount
                invoice = Invoice.objects.filter(
                    student=student,
                    balance__lte=amount + Decimal('100'),
                    balance__gte=amount - Decimal('100'),
                    status__in=['issued', 'partial', 'overdue']
                ).order_by('-created_at').first()

                return invoice

        except Exception as e:
            logger.error(f"Error in find_matching_invoice: {str(e)}")

        return None

    @staticmethod
    def process_mpesa_callback(transaction_id, amount, phone_number, reference_text, raw_data):
        """
        Process M-Pesa callback

        Args:
            transaction_id: str M-Pesa transaction ID
            amount: Decimal amount
            phone_number: str customer phone number
            reference_text: str reference/description
            raw_data: dict raw webhook data

        Returns:
            dict with 'status', 'message', 'invoice_id', 'payment_id'
        """
        try:
            # Create M-Pesa transaction record
            mpesa_tx = MpesaTransaction.objects.create(
                transaction_id=transaction_id,
                amount=amount,
                phone_number=phone_number,
                reference_text=reference_text,
                status='pending',
                raw_webhook_data=raw_data
            )

            # Find matching invoice
            invoice = MpesaService.find_matching_invoice(amount, phone_number)

            if not invoice:
                mpesa_tx.status = 'unmatched'
                mpesa_tx.save()
                logger.warning(
                    f"Could not match M-Pesa transaction {transaction_id} "
                    f"({amount} from {phone_number})"
                )
                return {
                    'status': 'unmatched',
                    'message': 'Could not match to any invoice',
                    'transaction_id': transaction_id
                }

            # Record payment
            payment = FeePayment.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method='mpesa',
                reference=transaction_id,
                status='completed'
            )

            # Update invoice
            invoice.amount_paid = invoice.amount_paid + amount
            invoice.balance = invoice.total_amount - invoice.amount_paid

            if invoice.balance == 0:
                invoice.status = 'paid'
            elif invoice.balance < invoice.total_amount:
                invoice.status = 'partial'

            invoice.save()

            # Update M-Pesa transaction
            mpesa_tx.status = 'processed'
            mpesa_tx.matched_invoice = invoice
            mpesa_tx.save()

            logger.info(
                f"M-Pesa payment processed: {transaction_id} "
                f"matched to invoice {invoice.id}"
            )

            return {
                'status': 'processed',
                'message': 'Payment recorded successfully',
                'invoice_id': invoice.id,
                'payment_id': payment.id,
                'transaction_id': transaction_id
            }

        except Exception as e:
            logger.error(f"Error in process_mpesa_callback: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'transaction_id': transaction_id
            }

    @staticmethod
    def verify_mpesa_signature(body, signature, secret_key):
        """
        Verify M-Pesa callback signature

        Args:
            body: str request body
            signature: str signature from headers
            secret_key: str M-Pesa API secret

        Returns:
            bool True if valid
        """
        import hmac
        import hashlib
        import base64

        try:
            computed_signature = base64.b64encode(
                hmac.new(
                    secret_key.encode(),
                    body.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()

            return computed_signature == signature
        except Exception as e:
            logger.error(f"Error verifying M-Pesa signature: {str(e)}")
            return False
