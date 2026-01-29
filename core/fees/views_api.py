from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum, Count
from decimal import Decimal
import json
import logging

from .models import (
    Term, FeeStructure, StudentFeeOverride, Invoice,
    FeePayment, PaymentReceipt, Arrears, MpesaTransaction
)
from .serializers import (
    TermSerializer, FeeStructureSerializer, StudentFeeOverrideSerializer,
    InvoiceListSerializer, InvoiceDetailSerializer, PaymentSerializer,
    PaymentReceiptSerializer, ArrearsSerializer, MpesaTransactionSerializer,
    BatchInvoiceGenerationSerializer, RecordPaymentSerializer, MpesaWebhookSerializer
)
from .services import (
    InvoiceGenerationService, PaymentService, ArrearsService, MpesaService
)
from core.users.models import Student

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.all()
    serializer_class = TermSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['academic_year', 'term_type']
    ordering_fields = ['academic_year', 'start_date']
    ordering = ['-academic_year', '-start_date']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return Term.objects.filter(school=user.school)
        return Term.objects.none()

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class FeeStructureViewSet(viewsets.ModelViewSet):
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'term__academic_year']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return FeeStructure.objects.filter(school=user.school)
        return FeeStructure.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """Create multiple fee structures at once"""
        fee_structures_data = request.data.get('fee_structures', [])
        created = []
        errors = []

        for fs_data in fee_structures_data:
            serializer = FeeStructureSerializer(data=fs_data)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                created.append(serializer.data)
            else:
                errors.append(serializer.errors)

        return Response({
            'created': created,
            'errors': errors,
            'total_created': len(created)
        }, status=status.HTTP_201_CREATED if not errors else status.HTTP_400_BAD_REQUEST)


class StudentFeeOverrideViewSet(viewsets.ModelViewSet):
    serializer_class = StudentFeeOverrideSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__user__first_name', 'student__user__last_name', 'reason']
    ordering_fields = ['created_at', 'override_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return StudentFeeOverride.objects.filter(student__school=user.school)
        return StudentFeeOverride.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'student__user__first_name', 'student__user__last_name']
    ordering_fields = ['created_at', 'due_date', 'balance', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return Invoice.objects.filter(student__school=user.school)
        return Invoice.objects.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InvoiceDetailSerializer
        return InvoiceListSerializer

    @action(detail=False, methods=['post'])
    def generate_batch(self, request):
        """Generate invoices for a term"""
        serializer = BatchInvoiceGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            results = InvoiceGenerationService.generate_invoices_for_term(
                term=serializer.validated_data['term'],
                school=serializer.validated_data.get('school'),
                class_assigned=serializer.validated_data.get('class'),
                user=request.user
            )
            return Response(results, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error generating invoices: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get invoice statistics"""
        queryset = self.get_queryset()
        stats_data = {
            'total_invoices': queryset.count(),
            'total_amount': queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0'),
            'total_paid': queryset.aggregate(Sum('amount_paid'))['amount_paid__sum'] or Decimal('0'),
            'total_balance': queryset.aggregate(Sum('balance'))['balance__sum'] or Decimal('0'),
            'by_status': dict(
                queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'overdue_count': queryset.filter(
                status='overdue',
                due_date__lt=timezone.now().date()
            ).count()
        }
        return Response(stats_data)

    @action(detail='id', methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid (admin override)"""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.save()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice__invoice_number', 'reference', 'payment_method']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return FeePayment.objects.filter(invoice__student__school=user.school)
        return FeePayment.objects.none()

    @action(detail=False, methods=['post'])
    def record_payment(self, request):
        """Record a new payment"""
        serializer = RecordPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = PaymentService.record_payment(
                invoice=serializer.validated_data['invoice'],
                amount=serializer.validated_data['amount'],
                payment_method=serializer.validated_data['payment_method'],
                reference=serializer.validated_data.get('reference', ''),
                user=request.user
            )
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error recording payment: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get payment statistics"""
        queryset = self.get_queryset()
        stats_data = {
            'total_payments': queryset.count(),
            'total_amount': queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal('0'),
            'by_method': dict(
                queryset.values('payment_method').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                ).values_list('payment_method', 'total')
            ),
            'by_status': dict(
                queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
            )
        }
        return Response(stats_data)


class PaymentReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentReceiptSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'email_sent_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return PaymentReceipt.objects.filter(
                payment__invoice__student__school=user.school
            )
        return PaymentReceipt.objects.none()

    @action(detail='id', methods=['post'])
    def send_email(self, request, pk=None):
        """Send receipt via email"""
        receipt = self.get_object()
        # This would typically call a Celery task
        # For now, just mark as sent
        from django.utils import timezone
        receipt.email_sent_at = timezone.now()
        receipt.save()
        return Response({'status': 'Email sent'})


class ArrearsViewSet(viewsets.ModelViewSet):
    serializer_class = ArrearsSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__user__first_name', 'student__user__last_name']
    ordering_fields = ['created_at', 'total_arrears', 'days_outstanding']
    ordering = ['-total_arrears']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            # Show only unresolved arrears by default
            show_resolved = self.request.query_params.get('show_resolved', 'false').lower() == 'true'
            queryset = Arrears.objects.filter(school=user.school)
            if not show_resolved:
                queryset = queryset.filter(is_resolved=False)
            return queryset
        return Arrears.objects.none()

    @action(detail='id', methods=['post'])
    def resolve(self, request, pk=None):
        """Mark arrears as resolved"""
        arrears = self.get_object()
        arrears.is_resolved = True
        arrears.resolved_date = timezone.now()
        arrears.notes = request.data.get('notes', '')
        arrears.save()
        return Response(self.get_serializer(arrears).data)

    @action(detail=False, methods=['post'])
    def update_all(self, request):
        """Update all arrears (typically called from Celery task)"""
        results = ArrearsService.update_all_arrears()
        return Response(results)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get arrears statistics"""
        queryset = self.get_queryset()
        stats_data = {
            'total_students_in_arrears': queryset.filter(is_resolved=False).count(),
            'total_arrears_amount': queryset.filter(is_resolved=False).aggregate(
                Sum('total_arrears')
            )['total_arrears__sum'] or Decimal('0'),
            'average_days_outstanding': queryset.filter(
                is_resolved=False
            ).aggregate(
                avg_days=Sum('days_outstanding') / Count('id')
            )['avg_days'] or 0,
            'by_days_range': {
                '0-30': queryset.filter(
                    days_outstanding__lte=30, is_resolved=False
                ).count(),
                '31-60': queryset.filter(
                    days_outstanding__gt=30,
                    days_outstanding__lte=60,
                    is_resolved=False
                ).count(),
                '61-90': queryset.filter(
                    days_outstanding__gt=60,
                    days_outstanding__lte=90,
                    is_resolved=False
                ).count(),
                '90+': queryset.filter(
                    days_outstanding__gt=90, is_resolved=False
                ).count()
            }
        }
        return Response(stats_data)


class MpesaTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MpesaTransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['transaction_id', 'phone_number', 'reference_text']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return MpesaTransaction.objects.filter(
                matched_invoice__student__school=user.school
            )
        return MpesaTransaction.objects.none()

    @action(detail='id', methods=['post'])
    def retry_match(self, request, pk=None):
        """Retry matching an unmatched M-Pesa transaction"""
        transaction = self.get_object()

        if transaction.status != 'unmatched':
            return Response(
                {'error': 'Can only retry unmatched transactions'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invoice = MpesaService.find_matching_invoice(
            transaction.amount,
            transaction.phone_number
        )

        if invoice:
            # Create payment
            payment = PaymentService.record_payment(
                invoice=invoice,
                amount=transaction.amount,
                payment_method='mpesa',
                reference=transaction.transaction_id
            )

            transaction.status = 'processed'
            transaction.matched_invoice = invoice
            transaction.save()

            return Response({
                'status': 'matched',
                'invoice_id': invoice.id,
                'payment_id': payment.id
            })

        return Response(
            {'error': 'Could not match to any invoice'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_webhook_handler(request):
    """
    Handle M-Pesa payment callbacks

    This endpoint is called by M-Pesa when a payment is received.
    It processes the callback and records the payment in the system.
    """
    try:
        # Parse webhook data
        webhook_data = request.data

        # Extract transaction details
        # This assumes M-Pesa sends data in a specific format
        # You'll need to adapt based on M-Pesa's actual callback structure
        if 'Body' in webhook_data:
            body = webhook_data['Body']
            result = body.get('stkCallback', {})
            if result.get('ResultCode') == 0:
                checkout_detail = result.get('CallbackMetadata', {}).get('Item', [])
                details = {item['Name']: item['Value'] for item in checkout_detail}

                transaction_id = details.get('MpesaReceiptNumber')
                amount = Decimal(str(details.get('Amount', 0)))
                phone_number = str(details.get('PhoneNumber', ''))
                reference_text = details.get('MerchantRequestID', '')
            else:
                return Response(
                    {'ResultCode': 1, 'ResultDesc': 'Payment failed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif 'Result' in webhook_data:
            result = webhook_data['Result']
            transaction_id = result.get('TransactionID')
            amount = Decimal(str(result.get('TransAmount', 0)))
            phone_number = str(result.get('MSISDN', ''))
            reference_text = result.get('TransRef', '')
        else:
            return Response(
                {'ResultCode': 1, 'ResultDesc': 'Invalid webhook format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process the callback
        result = MpesaService.process_mpesa_callback(
            transaction_id=transaction_id,
            amount=amount,
            phone_number=phone_number,
            reference_text=reference_text,
            raw_data=webhook_data
        )

        logger.info(f"M-Pesa callback processed: {result}")

        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Received'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error processing M-Pesa webhook: {str(e)}")
        return Response(
            {'ResultCode': 1, 'ResultDesc': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
