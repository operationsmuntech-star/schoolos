from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.users.models import Student, School, CustomUser, StudentClass


class Term(models.Model):
    """School terms/semesters"""
    TERM_CHOICES = (
        ('term1', 'Term 1'),
        ('term2', 'Term 2'),
        ('term3', 'Term 3'),
        ('january', 'January Module'),
        ('summer', 'Summer Module'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='terms')
    term_type = models.CharField(max_length=20, choices=TERM_CHOICES)
    academic_year = models.CharField(max_length=9)  # e.g., "2025/2026"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fees_term'
        unique_together = ('school', 'term_type', 'academic_year')
        ordering = ['-academic_year', '-start_date']
    
    def __str__(self):
        return f"{self.school.name} - {self.get_term_type_display()} {self.academic_year}"


class FeeStructure(models.Model):
    """Define fees per term/class/school"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_structures')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='fee_structures')
    class_assigned = models.ForeignKey(StudentClass, on_delete=models.CASCADE, related_name='fee_structures', null=True, blank=True)
    
    # If class_assigned is null, this is a school-wide fee
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    description = models.TextField()  # e.g., "Tuition", "Lab Fees", "Exam Fees"
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_fee_structures')
    
    class Meta:
        db_table = 'fees_structure'
        unique_together = ('school', 'term', 'class_assigned', 'description')
        ordering = ['due_date']
    
    def __str__(self):
        class_info = f" - {self.class_assigned.name}" if self.class_assigned else " (School-wide)"
        return f"{self.description} ({self.amount}) {class_info}"


class StudentFeeOverride(models.Model):
    """Override fee for specific student (e.g., scholarship, discount)"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_overrides')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_overrides')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    
    # If null, this fee is waived; otherwise use this amount
    override_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.00'))])
    reason = models.CharField(max_length=100)  # e.g., "Scholarship", "Discount", "Hardship"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_fee_overrides')
    
    class Meta:
        db_table = 'fees_student_override'
        unique_together = ('student', 'term', 'fee_structure')
    
    def __str__(self):
        return f"{self.student.user.first_name} - {self.fee_structure.description} Override: {self.override_amount or 'WAIVED'}"


class Invoice(models.Model):
    """Student invoice for a term"""
    INVOICE_STATUS = (
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Fully Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='invoices')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='invoices')
    
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)  # e.g., SCHOOL-2026-001-0001
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    
    class Meta:
        db_table = 'fees_invoice'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['school', 'student', 'term']),
            models.Index(fields=['status', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.student} ({self.status})"
    
    def save(self, *args, **kwargs):
        self.balance = self.total_amount - self.amount_paid
        if self.balance == 0:
            self.status = 'paid'
        elif self.balance < self.total_amount and self.amount_paid > 0:
            self.status = 'partial'
        super().save(*args, **kwargs)


class FeePayment(models.Model):
    """Payment transaction for fees (not to be confused with payments.Payment)"""
    PAYMENT_METHOD = (
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('other', 'Other'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='fee_payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    reference = models.CharField(max_length=100)  # M-Pesa code, check #, etc.
    
    # M-Pesa specific fields
    mpesa_transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="M-Pesa transaction ID from provider")
    mpesa_callback_json = models.JSONField(default=dict, blank=True, help_text="Raw M-Pesa callback data")
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='completed')
    
    payment_date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fees_payment'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['invoice', 'status']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.invoice} - {self.amount} ({self.get_payment_method_display()})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-update invoice balance when payment is completed
        if self.status == 'completed':
            self.invoice.amount_paid += self.amount
            self.invoice.save()


class PaymentReceipt(models.Model):
    """Generated receipt for fee payment"""
    fee_payment = models.OneToOneField(FeePayment, on_delete=models.CASCADE, related_name='receipt')
    
    receipt_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='receipts/%Y/%m/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_sent_to = models.EmailField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fees_payment_receipt'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Receipt {self.receipt_number}"


class Arrears(models.Model):
    """Track overdue fees per student"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='arrears')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='arrears')
    
    total_arrears = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    days_outstanding = models.IntegerField(default=0)
    
    first_arrears_date = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'fees_arrears'
        unique_together = ('school', 'student')
        ordering = ['-total_arrears']
    
    def __str__(self):
        return f"{self.student} - Arrears: {self.total_arrears}"
    
    def update_days_outstanding(self):
        """Calculate days outstanding"""
        if not self.is_resolved:
            self.days_outstanding = (timezone.now().date() - self.first_arrears_date).days
            self.save()


class MpesaTransaction(models.Model):
    """Log M-Pesa webhook transactions for audit trail"""
    STATUS = (
        ('pending', 'Pending'),
        ('matched', 'Matched to Invoice'),
        ('unmatched', 'No Invoice Match'),
        ('processed', 'Payment Created'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='mpesa_transactions', null=True, blank=True)
    
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=20)
    reference_text = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    matched_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='mpesa_transactions')
    
    raw_webhook_data = models.JSONField()
    
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_mpesa_transactions')
    
    class Meta:
        db_table = 'fees_mpesa_transaction'
        ordering = ['-received_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} ({self.status})"
