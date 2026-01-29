from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Term, FeeStructure, StudentFeeOverride, Invoice, 
    FeePayment, PaymentReceipt, Arrears, MpesaTransaction
)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('school', 'term_type', 'academic_year', 'start_date', 'end_date', 'is_active')
    list_filter = ('school', 'term_type', 'academic_year', 'is_active')
    search_fields = ('school__name', 'academic_year')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('school', 'term_type', 'academic_year')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class FeeStructureInline(admin.TabularInline):
    model = FeeStructure
    extra = 1
    fields = ('description', 'amount', 'class_assigned', 'due_date', 'is_active')


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('school', 'term', 'description', 'amount_display', 'class_assigned', 'due_date', 'is_active')
    list_filter = ('school', 'term', 'is_active', 'due_date')
    search_fields = ('school__name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Fee Info', {
            'fields': ('school', 'term', 'description', 'amount')
        }),
        ('Application', {
            'fields': ('class_assigned',),
            'description': 'Leave blank for school-wide fees'
        }),
        ('Due Date', {
            'fields': ('due_date',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return f"{obj.school.currency} {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StudentFeeOverride)
class StudentFeeOverrideAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'override_amount_display', 'reason', 'created_at')
    list_filter = ('school', 'term', 'reason', 'created_at')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'reason')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Student & Fee', {
            'fields': ('school', 'student', 'term', 'fee_structure')
        }),
        ('Override', {
            'fields': ('override_amount', 'reason'),
            'description': 'Leave amount blank to waive this fee'
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def override_amount_display(self, obj):
        if obj.override_amount is None:
            return format_html('<span style="color: red;"><b>WAIVED</b></span>')
        return f"{obj.school.currency} {obj.override_amount:,.2f}"
    override_amount_display.short_description = 'Override Amount'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    fields = ('amount', 'payment_method', 'reference', 'status', 'payment_date')
    readonly_fields = ('payment_date', 'created_at')
    can_delete = False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'term', 'total_amount_display', 'amount_paid_display', 'balance_display', 'status_badge', 'due_date')
    list_filter = ('school', 'status', 'term', 'due_date')
    search_fields = ('invoice_number', 'student__user__first_name', 'student__user__last_name')
    readonly_fields = ('invoice_number', 'balance', 'created_at', 'updated_at', 'created_by')
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Invoice Info', {
            'fields': ('invoice_number', 'school', 'student', 'term')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'amount_paid', 'balance')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_amount_display(self, obj):
        return f"{obj.school.currency} {obj.total_amount:,.2f}"
    total_amount_display.short_description = 'Total Amount'
    
    def amount_paid_display(self, obj):
        color = 'green' if obj.amount_paid > 0 else 'gray'
        return format_html(f'<span style="color: {color};"><b>{obj.school.currency} {obj.amount_paid:,.2f}</b></span>')
    amount_paid_display.short_description = 'Amount Paid'
    
    def balance_display(self, obj):
        if obj.balance == 0:
            color = 'green'
        elif obj.balance < obj.total_amount:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<span style="color: {color};"><b>{obj.school.currency} {obj.balance:,.2f}</b></span>')
    balance_display.short_description = 'Balance'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#gray',
            'issued': '#blue',
            'paid': '#green',
            'partial': '#orange',
            'overdue': '#red',
            'cancelled': '#gray',
        }
        color = colors.get(obj.status, '#gray')
        return format_html(f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px;">{obj.get_status_display()}</span>')
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            # Generate invoice number if not provided
            if not obj.invoice_number:
                last_invoice = Invoice.objects.filter(school=obj.school).order_by('-id').first()
                counter = (last_invoice.invoice_number.split('-')[-1] if last_invoice else '000')
                new_counter = str(int(counter) + 1).zfill(4)
                obj.invoice_number = f"{obj.school.slug.upper()}-{obj.term.academic_year.replace('/', '')}-{new_counter}"
        super().save_model(request, obj, form, change)


@admin.register(FeePayment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'invoice', 'amount_display', 'payment_method', 'status_badge', 'payment_date')
    list_filter = ('school', 'payment_method', 'status', 'payment_date')
    search_fields = ('reference', 'invoice__invoice_number', 'invoice__student__user__first_name')
    readonly_fields = ('payment_date', 'created_at', 'updated_at', 'recorded_by')
    
    fieldsets = (
        ('Payment Info', {
            'fields': ('school', 'invoice', 'amount')
        }),
        ('Details', {
            'fields': ('payment_method', 'reference', 'status', 'notes')
        }),
        ('Recorded By', {
            'fields': ('recorded_by', 'payment_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return f"{obj.school.currency} {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'completed': '#008000',
            'failed': '#FF0000',
            'refunded': '#808080',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px;">{obj.get_status_display()}</span>')
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'payment_link', 'generated_at', 'email_status')
    list_filter = ('generated_at', 'email_sent_at')
    search_fields = ('receipt_number', 'payment__invoice__invoice_number')
    readonly_fields = ('generated_at', 'receipt_number')
    
    def payment_link(self, obj):
        return format_html(f'<a href="/admin/fees/payment/{obj.payment.id}/">{obj.payment.reference}</a>')
    payment_link.short_description = 'Payment Reference'
    
    def email_status(self, obj):
        if obj.email_sent_at:
            return format_html(f'<span style="color: green;"><b>✓ Sent to {obj.email_sent_to}</b></span>')
        return format_html('<span style="color: orange;">Pending</span>')
    email_status.short_description = 'Email Status'


@admin.register(Arrears)
class ArrearsAdmin(admin.ModelAdmin):
    list_display = ('student', 'school', 'total_arrears_display', 'days_outstanding', 'is_resolved_badge', 'first_arrears_date')
    list_filter = ('school', 'is_resolved', 'first_arrears_date')
    search_fields = ('student__user__first_name', 'student__user__last_name')
    readonly_fields = ('first_arrears_date', 'last_updated', 'days_outstanding')
    
    fieldsets = (
        ('Student Info', {
            'fields': ('school', 'student')
        }),
        ('Arrears Details', {
            'fields': ('total_arrears', 'days_outstanding', 'first_arrears_date', 'last_updated')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_date', 'notes')
        }),
    )
    
    def total_arrears_display(self, obj):
        return f"{obj.school.currency} {obj.total_arrears:,.2f}"
    total_arrears_display.short_description = 'Total Arrears'
    
    def is_resolved_badge(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: green;"><b>✓ Resolved</b></span>')
        return format_html('<span style="color: red;"><b>Outstanding</b></span>')
    is_resolved_badge.short_description = 'Status'


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'amount_display', 'phone_number', 'status_badge', 'received_at')
    list_filter = ('school', 'status', 'received_at')
    search_fields = ('transaction_id', 'phone_number', 'reference_text')
    readonly_fields = ('received_at', 'raw_webhook_data', 'transaction_id')
    
    fieldsets = (
        ('M-Pesa Info', {
            'fields': ('transaction_id', 'amount', 'phone_number', 'reference_text')
        }),
        ('Matching', {
            'fields': ('school', 'matched_invoice', 'status')
        }),
        ('Processing', {
            'fields': ('processed_at', 'processed_by'),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('raw_webhook_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('received_at',),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return f"KES {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'matched': '#4169E1',
            'unmatched': '#FF6347',
            'processed': '#008000',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px;">{obj.get_status_display()}</span>')
    status_badge.short_description = 'Status'
