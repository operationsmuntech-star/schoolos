# Finance Engine API Documentation

## Overview

The Finance Engine is the backbone of MunTech's school operating system. It provides complete financial management including fee structures, invoicing, payment processing, and M-Pesa integration.

## Architecture

### 8-Model Finance Pipeline

```
School
  ├─ Terms (academic periods)
  │   └─ FeeStructures (school-wide or class-specific)
  │       └─ StudentFeeOverrides (scholarships, discounts, waivers)
  │           └─ Invoices (auto-generated per student/term)
  │               └─ Payments (cash, bank, M-Pesa, check)
  │                   └─ PaymentReceipts (auto-generated PDFs)
  │
  └─ Arrears (tracking overdue fees)
      └─ MpesaTransaction (webhook audit trail)
```

### Core Models

#### 1. **Term**
Defines academic periods (terms, semesters, modules).

```python
Term.objects.create(
    school=school,
    term_type='term1',           # 'term1', 'term2', 'term3', 'january', 'summer'
    academic_year='2025/2026',
    start_date='2025-01-15',
    end_date='2025-04-15',
    is_active=True
)
```

#### 2. **FeeStructure**
Defines fees per school, term, and optionally per class.

```python
FeeStructure.objects.create(
    school=school,
    term=term,
    class_assigned=class_object,  # None for school-wide fees
    amount=50000,                  # Fees for the term
    description='Term 1 Fees',
    due_date='2025-02-15',
    created_by=user
)
```

#### 3. **StudentFeeOverride**
Handle scholarships, discounts, and waivers per student.

```python
# Scholarship (reduced amount)
StudentFeeOverride.objects.create(
    student=student,
    term=term,
    fee_structure=fee_structure,
    override_amount=Decimal('30000'),  # 60% scholarship
    reason='Merit Scholarship',
    created_by=user
)

# Full waiver (null amount_override)
StudentFeeOverride.objects.create(
    student=student,
    term=term,
    fee_structure=fee_structure,
    override_amount=None,              # Waived
    reason='Orphan',
    created_by=user
)
```

#### 4. **Invoice**
Auto-generated student invoices with balance tracking.

- **Auto-calculated balance**: `balance = total_amount - amount_paid`
- **Status tracking**: draft → issued → partial → paid/overdue/cancelled
- **Auto-numbering**: `{school-slug}-{academic-year}-{counter}` (e.g., `joyland-2025-0001`)

```python
# Generated via batch API or service
invoice = Invoice.objects.create(
    student=student,
    term=term,
    total_amount=Decimal('50000'),
    amount_paid=Decimal('0'),
    balance=Decimal('50000'),
    status='issued',
    created_by=user
)
```

#### 5. **Payment**
Payment transaction records (cash, bank, M-Pesa, check).

```python
payment = Payment.objects.create(
    invoice=invoice,
    amount=Decimal('25000'),
    payment_method='mpesa',  # 'mpesa', 'bank', 'cash', 'check'
    reference='LIB123ABC456',
    status='completed',
    recorded_by=user
)

# Auto-updates invoice
# - invoice.amount_paid += payment.amount
# - invoice.balance = total - amount_paid
# - invoice.status updated based on balance
```

#### 6. **PaymentReceipt**
Generated after successful payment.

```python
receipt = PaymentReceipt.objects.create(
    payment=payment,
    receipt_number='RCP-2025-001',  # Auto-generated
    # Async task generates PDF
)

# Track email delivery
receipt.email_sent_at = timezone.now()
receipt.email_sent_to = 'parent@example.com'
receipt.save()
```

#### 7. **Arrears**
Track students with overdue fees.

```python
arrears = Arrears.objects.create(
    student=student,
    school=school,
    total_arrears=Decimal('50000'),
    days_outstanding=45,
    is_resolved=False
)

# Update when invoices are paid
arrears.is_resolved = True
arrears.resolved_date = timezone.now()
arrears.save()
```

#### 8. **MpesaTransaction**
Webhook audit trail for M-Pesa payments.

```python
mpesa_tx = MpesaTransaction.objects.create(
    transaction_id='LIB123ABC456',
    amount=Decimal('50000'),
    phone_number='0712345678',
    reference_text='Invoice ABC123',
    status='pending',
    raw_webhook_data={...}
)

# After matching to invoice and recording payment
mpesa_tx.status = 'processed'
mpesa_tx.matched_invoice = invoice
mpesa_tx.save()
```

## API Endpoints

All endpoints require authentication (`IsAuthenticated` permission).

### Terms
```
GET    /fees/api/terms/                    # List all terms
POST   /fees/api/terms/                    # Create new term
GET    /fees/api/terms/{id}/               # Retrieve term
PUT    /fees/api/terms/{id}/               # Update term
DELETE /fees/api/terms/{id}/               # Delete term
```

### Fee Structures
```
GET    /fees/api/fee-structures/           # List structures
POST   /fees/api/fee-structures/           # Create structure
POST   /fees/api/fee-structures/batch_create/  # Batch create
GET    /fees/api/fee-structures/{id}/      # Retrieve
PUT    /fees/api/fee-structures/{id}/      # Update
DELETE /fees/api/fee-structures/{id}/      # Delete
```

### Invoices
```
GET    /fees/api/invoices/                 # List invoices
GET    /fees/api/invoices/stats/           # Invoice statistics
POST   /fees/api/invoices/generate_batch/  # Generate invoices from term
GET    /fees/api/invoices/{id}/            # Retrieve invoice details
POST   /fees/api/invoices/{id}/mark_paid/  # Mark as paid
```

**Generate Invoices:**
```bash
POST /fees/api/invoices/generate_batch/
{
    "term_id": 1,
    "school_id": 1,
    "class_id": null  # Optional, null = all classes
}

Response:
{
    "created": 45,
    "skipped": 2,
    "errors": []
}
```

### Payments
```
GET    /fees/api/payments/                 # List payments
GET    /fees/api/payments/stats/           # Payment statistics
POST   /fees/api/payments/record_payment/  # Record payment
```

**Record Payment:**
```bash
POST /fees/api/payments/record_payment/
{
    "invoice_id": 1,
    "amount": "25000.00",
    "payment_method": "mpesa",
    "reference": "LIB123ABC456"
}

Response:
{
    "id": 1,
    "invoice": 1,
    "amount": "25000.00",
    "payment_method": "mpesa",
    "status": "completed",
    ...
}
```

### Arrears
```
GET    /fees/api/arrears/                  # List (default: unresolved only)
GET    /fees/api/arrears/?show_resolved=true  # Include resolved
GET    /fees/api/arrears/stats/            # Arrears statistics
POST   /fees/api/arrears/{id}/resolve/     # Mark as resolved
POST   /fees/api/arrears/update_all/       # Recalculate all
```

### M-Pesa Transactions
```
GET    /fees/api/mpesa-transactions/       # List transactions
POST   /fees/api/mpesa-transactions/{id}/retry_match/  # Retry matching
```

## Business Logic Services

### 1. InvoiceGenerationService

Generate invoices in bulk from fee structures.

```python
from core.fees.services import InvoiceGenerationService

results = InvoiceGenerationService.generate_invoices_for_term(
    term=term,
    school=school,
    class_assigned=None,  # None = all classes
    user=request.user
)

# Returns: {'created': 45, 'skipped': 2, 'errors': [...]}
```

### 2. PaymentService

Record payments and auto-update invoices and arrears.

```python
from core.fees.services import PaymentService

payment = PaymentService.record_payment(
    invoice=invoice,
    amount=Decimal('25000'),
    payment_method='mpesa',
    reference='LIB123ABC456',
    user=request.user
)

# Auto-updates:
# - invoice.amount_paid
# - invoice.balance
# - invoice.status
# - arrears record (if resolved)
```

### 3. ArrearsService

Calculate and update arrears for students.

```python
from core.fees.services import ArrearsService

# Update single student
results = ArrearsService.update_arrears_for_student(student)

# Update all students (Celery task)
results = ArrearsService.update_all_arrears()

# Returns: {'created': X, 'updated': Y}
```

### 4. MpesaService

M-Pesa payment integration and webhook handling.

```python
from core.fees.services import MpesaService

# Find matching invoice
invoice = MpesaService.find_matching_invoice(
    amount=Decimal('50000'),
    phone_number='0712345678'
)

# Process webhook callback
result = MpesaService.process_mpesa_callback(
    transaction_id='LIB123ABC456',
    amount=Decimal('50000'),
    phone_number='0712345678',
    reference_text='...',
    raw_data={...}
)

# Returns:
# {'status': 'processed', 'invoice_id': 1, 'payment_id': 1, ...}
# OR
# {'status': 'unmatched', 'message': 'Could not match...'}
```

## M-Pesa Webhook Integration

### Setup

1. Configure M-Pesa API credentials in `.env`:
```
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/fees/api/mpesa/webhook/
```

2. Register webhook URL with M-Pesa (Daraja portal)

### Webhook Handler

**Endpoint:** `POST /fees/api/mpesa/webhook/`

The webhook handler:
1. Receives M-Pesa callback
2. Creates MpesaTransaction record (status=pending)
3. Attempts to match to invoice by phone + amount
4. If matched:
   - Creates Payment record
   - Updates Invoice (balance, status)
   - Sets MpesaTransaction status=processed
5. If unmatched:
   - Sets MpesaTransaction status=unmatched
   - Can be manually matched via `/mpesa-transactions/{id}/retry_match/`

## Workflows

### Workflow 1: Generate Monthly Invoices

```python
from core.fees.services import InvoiceGenerationService

# For Term 1
results = InvoiceGenerationService.generate_invoices_for_term(
    term=Term.objects.get(academic_year='2025/2026', term_type='term1'),
    school=school,
    user=request.user
)

# POST /fees/api/invoices/generate_batch/
# {
#     "term_id": 1,
#     "school_id": 1
# }
```

### Workflow 2: Record M-Pesa Payment

```
1. Parent sends 50,000 KES via M-Pesa to shortcode
2. M-Pesa webhook calls /fees/api/mpesa/webhook/
3. System auto-matches to student's invoice
4. Payment recorded, invoice updated
5. Parent receives SMS receipt
```

### Workflow 3: Track Arrears

```python
# Nightly Celery task
@periodic_task(run_every=crontab(hour=2, minute=0))
def update_student_arrears():
    from core.fees.services import ArrearsService
    results = ArrearsService.update_all_arrears()
    return results

# View overdue students
GET /fees/api/arrears/?days_outstanding__gte=30

# Dashboard query
arrears = Arrears.objects.filter(
    school=school,
    is_resolved=False
).order_by('-days_outstanding')
```

## Admin Interface Features

All models have comprehensive admin interfaces with:

- **Color-coded status badges**: Green (paid), Red (overdue), Orange (partial), Blue (issued)
- **Auto-generated invoice numbers**: `school-slug-academic-year-counter`
- **Currency formatting**: Respects school's currency setting
- **Inline displays**: See payments directly in invoice detail
- **Email tracking**: Know if receipts were sent
- **Collapsible audit sections**: created_by, created_at, updated_at
- **Filter by status**: Quick access to overdue, partial, etc.

## Settings Configuration

Add to `settings.py` if needed:

```python
# Finance Engine
FINANCE_ENGINE = {
    'AUTO_GENERATE_RECEIPTS': True,  # Auto-generate PDFs after payment
    'EMAIL_RECEIPTS': True,           # Auto-email receipts
    'SMS_ALERTS': True,               # Send SMS on overdue
    'ARREARS_THRESHOLD_DAYS': 30,     # Days before flagging as arrears
}
```

## Next Steps

1. **Notifications Layer**: SMS alerts for overdue fees via Celery
2. **Parent Portal**: API endpoints for parent app to view fees/payments
3. **Receipt PDF Generation**: Async task via Celery
4. **Advanced Reporting**: Dashboard with fee analytics, collection rates
5. **Timetabling Engine**: Class scheduling and resource allocation
6. **Offline/LAN Mode**: Sync invoices when internet available

---

**System of Record Philosophy:**
MunTech's Finance Engine is the single source of truth for all school finances. Every transaction is auditable, every invoice is traceable, and every payment is verifiable. This is the spine upon which parent trust and school operations depend.
