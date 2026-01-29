from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import (
    Term, FeeStructure, StudentFeeOverride, Invoice,
    FeePayment, PaymentReceipt, Arrears, MpesaTransaction
)
from core.users.models import Student, School


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = [
            'id', 'school', 'term_type', 'academic_year', 'start_date',
            'end_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FeeStructureSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    class_name = serializers.CharField(source='class_assigned.name', read_only=True, allow_null=True)

    class Meta:
        model = FeeStructure
        fields = [
            'id', 'school', 'school_name', 'term', 'class_assigned', 'class_name',
            'amount', 'description', 'due_date', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class StudentFeeOverrideSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    fee_description = serializers.CharField(source='fee_structure.description', read_only=True)
    override_type = serializers.SerializerMethodField()

    class Meta:
        model = StudentFeeOverride
        fields = [
            'id', 'student', 'student_name', 'term', 'fee_structure', 'fee_description',
            'override_amount', 'override_type', 'reason', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_override_type(self, obj):
        if obj.override_amount is None:
            return 'WAIVED'
        return 'DISCOUNTED'


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

    class Meta:
        model = FeePayment
        fields = [
            'id', 'invoice', 'amount', 'payment_method', 'payment_method_display',
            'reference', 'status', 'status_display', 'recorded_by', 'recorded_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at', 'updated_at']


class PaymentReceiptSerializer(serializers.ModelSerializer):
    payment_details = PaymentSerializer(source='fee_payment', read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = [
            'id', 'fee_payment', 'payment_details', 'receipt_number', 'pdf_file',
            'email_sent_at', 'email_sent_to', 'created_at'
        ]
        read_only_fields = ['id', 'receipt_number', 'created_at']


class InvoiceDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    school_name = serializers.CharField(source='student.school.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fee_payments = PaymentSerializer(many=True, read_only=True)
    amount_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'student', 'student_name', 'school_name',
            'term', 'total_amount', 'amount_paid', 'balance', 'amount_due',
            'status', 'status_display', 'due_date', 'fee_payments',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'amount_paid', 'balance', 'created_by',
            'created_at', 'updated_at'
        ]


class InvoiceListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'student', 'student_name', 'term',
            'total_amount', 'amount_paid', 'balance', 'status', 'status_display',
            'due_date', 'created_at'
        ]
        read_only_fields = fields


class ArrearsSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    is_resolved_display = serializers.SerializerMethodField()

    class Meta:
        model = Arrears
        fields = [
            'id', 'student', 'student_name', 'school', 'school_name',
            'total_arrears', 'days_outstanding', 'is_resolved', 'is_resolved_display',
            'resolved_date', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'days_outstanding', 'created_at', 'updated_at'
        ]

    def get_is_resolved_display(self, obj):
        return 'Resolved' if obj.is_resolved else 'Outstanding'


class MpesaTransactionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MpesaTransaction
        fields = [
            'id', 'transaction_id', 'amount', 'phone_number', 'reference_text',
            'status', 'status_display', 'matched_invoice', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BatchInvoiceGenerationSerializer(serializers.Serializer):
    """Serializer for batch invoice generation"""
    term_id = serializers.IntegerField()
    school_id = serializers.IntegerField()
    class_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        try:
            term = Term.objects.get(id=data['term_id'])
        except Term.DoesNotExist:
            raise serializers.ValidationError({'term_id': 'Term not found'})

        try:
            school = School.objects.get(id=data['school_id'])
        except School.DoesNotExist:
            raise serializers.ValidationError({'school_id': 'School not found'})

        data['term'] = term
        data['school'] = school
        return data


class RecordPaymentSerializer(serializers.Serializer):
    """Serializer for recording payments"""
    invoice_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=['mpesa', 'bank', 'cash', 'check'])
    reference = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0')
        return value

    def validate(self, data):
        try:
            invoice = Invoice.objects.get(id=data['invoice_id'])
        except Invoice.DoesNotExist:
            raise serializers.ValidationError({'invoice_id': 'Invoice not found'})

        if data['amount'] > invoice.balance:
            raise serializers.ValidationError(
                {'amount': f'Payment exceeds balance of {invoice.balance}'}
            )

        data['invoice'] = invoice
        return data


class MpesaWebhookSerializer(serializers.Serializer):
    """Serializer for M-Pesa webhook data"""
    Result = serializers.DictField(required=False)
    Body = serializers.DictField(required=False)

    def validate(self, data):
        # M-Pesa sends either Result or Body depending on callback type
        if not data.get('Result') and not data.get('Body'):
            raise serializers.ValidationError('Invalid M-Pesa webhook data')
        return data
