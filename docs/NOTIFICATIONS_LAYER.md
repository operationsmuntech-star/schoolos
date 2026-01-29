# Notifications Layer - Complete Documentation

## Overview

The Notifications Layer is the **communication backbone** of MunTech's School Operating System. It automatically sends SMS and email alerts to parents about critical school events: invoice issuance, payment received, arrears alerts, payment reminders, and exam results.

**Architecture: Event-Driven + Queue-Based**
- Events triggered by Finance Engine and other systems
- Messages queued for async delivery via Celery
- Provider-agnostic (Africa's Talking, Twilio, built-in SMTP)
- Template-based for multi-language support
- Recipient preferences respected (quiet hours, opt-out)

## 5 Core Models

### 1. NotificationPreference
**Purpose:** Parent's notification settings

```python
prefs = NotificationPreference.objects.create(
    parent=user,
    sms_enabled=True,
    email_enabled=True,
    phone_number='0712345678',
    # Event preferences
    invoice_issued=True,
    payment_received=True,
    arrears_warning=True,
    arrears_critical=True,
    payment_reminder=True,
    exam_results=False,
    attendance_alert=True,
    language='en',  # or 'sw' for Swahili
    # Quiet hours (don't send between these times)
    quiet_hours_start='22:00',  # 10 PM
    quiet_hours_end='07:00',    # 7 AM
)
```

**Features:**
- Multi-channel support (SMS, Email, both)
- Per-event opt-in/opt-out
- Quiet hours (don't disturb period)
- Language preference (English, Swahili)
- Automatic quiet hours check before sending

### 2. Notification
**Purpose:** Track all notifications sent to parents

```python
notification = Notification.objects.create(
    recipient=parent_user,
    event_type='invoice_issued',  # or payment_received, arrears_warning, etc.
    title='Invoice 2025-001 Issued',
    message='An invoice for KES 50,000 has been issued for John Doe',
    student=student_obj,
    invoice=invoice_obj,
    payment=None,
    arrears=None,
    data={
        'invoice_number': 'JOYLAND-2025-0001',
        'amount': '50000.00',
        'due_date': '2025-02-15',
    }
)
```

**Fields:**
- `recipient`: Parent to receive notification
- `event_type`: Type of event (7 choices)
- `title`, `message`: Notification content
- `student`, `invoice`, `payment`, `arrears`: Related objects
- `data`: JSON metadata for templating
- `is_read`, `read_at`: Engagement tracking
- Auto-indexed for fast querying

### 3. SMSLog
**Purpose:** Track SMS messages sent

```python
sms = SMSLog.objects.create(
    notification=notification,
    phone_number='0712345678',
    message='Invoice KES 50,000 issued for John. Due: Feb 15. Reply PAID to confirm.',
    status='queued',  # queued → sent → delivered OR failed → bounced
    provider='africas-talking',
    attempt_count=0,
    max_retries=3
)
```

**Features:**
- Status tracking: queued → sent → delivered (or failed)
- Automatic retry with exponential backoff
- Provider tracking (which SMS service sent it)
- Error logging with error codes
- Message length tracking

**Retry Logic:**
- Failed SMS can be retried up to 3 times
- Retry delay: 60s * (attempt + 1)
- Manual retry via API: `POST /notifications/api/sms-logs/{id}/retry/`

### 4. EmailLog
**Purpose:** Track email messages sent

```python
email = EmailLog.objects.create(
    notification=notification,
    recipient_email='john.doe@example.com',
    subject='Invoice 2025-001 Issued',
    message_html='<html>...</html>',
    status='queued',
    provider='django-email',
    attempt_count=0,
    max_retries=3
)
```

**Features:**
- Same retry logic as SMS
- Engagement tracking: `opened_at`, `clicked_at`
- HTML email support
- Provider tracking
- Error handling and logging

### 5. NotificationTemplate
**Purpose:** Reusable templates for multi-language notifications

```python
template = NotificationTemplate.objects.create(
    school=school,  # Null = system-wide template
    event_type='invoice_issued',
    language='en',
    title='Invoice Issued',
    sms_template='Invoice {{invoice_number}} (KES {{amount}}) due {{due_date}}',
    email_subject='Invoice {{invoice_number}} - KES {{amount}}',
    email_template='<h1>Invoice Issued</h1><p>An invoice for {{amount}} has been issued...</p>',
    variables=['invoice_number', 'amount', 'due_date', 'student_name'],
    is_active=True
)
```

**Template Variables:**
- Automatic: `parent_name`, `school_name`
- Finance: `student_name`, `amount`, `due_date`, `days_outstanding`, `invoice_number`
- Custom: Can add to `data` field on Notification
- Syntax: `{{variable_name}}`

## API Endpoints

### Notification Preferences
```
GET    /notifications/api/preferences/     # Get/create own preferences
PUT    /notifications/api/preferences/     # Update preferences
POST   /notifications/api/preferences/test_sms/  # Send test SMS
```

**Get/Update Preferences:**
```bash
GET /notifications/api/preferences/
{
    "sms_enabled": true,
    "email_enabled": true,
    "phone_number": "0712345678",
    "invoice_issued": true,
    "payment_received": true,
    "arrears_warning": true,
    "arrears_critical": true,
    "payment_reminder": true,
    "exam_results": false,
    "attendance_alert": true,
    "language": "en",
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00"
}

PUT /notifications/api/preferences/
{
    "sms_enabled": false,  # Disable SMS
    "quiet_hours_start": "21:00"  # Change quiet hours
}
```

### Notifications (Inbox)
```
GET    /notifications/api/notifications/          # List all
GET    /notifications/api/notifications/{id}/     # Get details
POST   /notifications/api/notifications/{id}/mark_as_read/  # Mark read
POST   /notifications/api/notifications/mark_all_as_read/   # Mark all read
GET    /notifications/api/notifications/unread_count/       # Count unread
GET    /notifications/api/notifications/stats/              # Statistics
```

**List Notifications:**
```bash
GET /notifications/api/notifications/?ordering=-created_at&is_read=false
```

**Notification Object:**
```json
{
    "id": 1,
    "recipient": 5,
    "recipient_name": "John Doe",
    "event_type": "invoice_issued",
    "event_type_display": "Invoice Issued",
    "title": "Invoice 2025-001 Issued",
    "message": "An invoice for KES 50,000 has been issued...",
    "student": 1,
    "student_name": "Jane Doe",
    "invoice": 1,
    "payment": null,
    "arrears": null,
    "is_read": false,
    "read_at": null,
    "data": {"invoice_number": "JOYLAND-2025-0001", "amount": "50000.00"},
    "created_at": "2025-01-28T10:30:00Z",
    "updated_at": "2025-01-28T10:30:00Z"
}
```

**Unread Count:**
```bash
GET /notifications/api/notifications/unread_count/
{"unread_count": 3}
```

**Statistics:**
```bash
GET /notifications/api/notifications/stats/
{
    "total": 15,
    "unread": 3,
    "by_event_type": {
        "invoice_issued": 5,
        "payment_received": 4,
        "arrears_warning": 3,
        "arrears_critical": 2,
        "payment_reminder": 1
    },
    "by_date": {
        "today": 2,
        "this_week": 8,
        "this_month": 15
    }
}
```

### SMS & Email Logs
```
GET    /notifications/api/sms-logs/           # List SMS logs
GET    /notifications/api/sms-logs/{id}/      # SMS details
POST   /notifications/api/sms-logs/{id}/retry/  # Retry failed SMS

GET    /notifications/api/email-logs/         # List email logs
GET    /notifications/api/email-logs/{id}/    # Email details
POST   /notifications/api/email-logs/{id}/retry/  # Retry failed email
```

**SMS/Email Log Object:**
```json
{
    "id": 1,
    "notification": 1,
    "phone_number": "0712345678",
    "message": "Invoice KES 50,000 due Feb 15...",
    "status": "sent",
    "status_display": "Sent",
    "provider": "africas-talking",
    "provider_message_id": "ATM123456",
    "attempt_count": 1,
    "max_retries": 3,
    "can_retry": false,
    "error_message": "",
    "error_code": "",
    "created_at": "2025-01-28T10:30:00Z",
    "sent_at": "2025-01-28T10:31:00Z",
    "delivered_at": "2025-01-28T10:31:15Z"
}
```

## Service Layer

### NotificationService (Central Hub)

```python
from core.notifications.services import NotificationService

# 1. Check if should notify
should_send = NotificationService.should_notify(
    parent_user,
    'invoice_issued'
)

# 2. Get enabled channels
channels = NotificationService.get_channels(parent_user)  # ['sms', 'email']

# 3. Create notification
notification = NotificationService.create_notification(
    recipient=parent_user,
    event_type='invoice_issued',
    title='Invoice Issued',
    message='Invoice for KES 50,000 issued',
    student=student,
    invoice=invoice,
    data={'amount': '50000', 'due_date': '2025-02-15'}
)

# 4. Dispatch through channels
results = NotificationService.dispatch_notification(
    notification,
    channels=['sms', 'email']
)
# Returns: {'sms': SMSLog, 'email': EmailLog}
```

### SMSService (SMS Sending)

**Providers Supported:**
- **Africa's Talking** (recommended for Africa)
- **Twilio** (global, high reliability)
- Custom provider (override `_send_generic`)

**Configuration (.env):**
```
SMS_PROVIDER=africas-talking
AFRICAS_TALKING_API_KEY=your_api_key
AFRICAS_TALKING_USERNAME=your_username

# OR
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
```

**Usage:**
```python
from core.notifications.services import SMSService

# Send via provider (async via Celery)
result = SMSService.send_via_provider(sms_log)
# Returns: {'success': True, 'message_id': 'ABC123'}
# OR: {'success': False, 'error_message': '...', 'error_code': 'SMS_FAILED'}
```

### EmailService (Email Sending)

**Configuration (.env):**
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=noreply@muntech.school
```

**Usage:**
```python
from core.notifications.services import EmailService

# Send via provider (async via Celery)
result = EmailService.send_via_provider(email_log)
# Returns: {'success': True}
# OR: {'success': False, 'error_message': '...'}
```

## Celery Tasks (Background Jobs)

**All tasks run on schedule via Celery Beat (automatic)**

### 1. send_pending_sms
- **Schedule:** Every 5 minutes
- **Function:** Send all queued SMS
- **Auto-retry:** Failed SMS retried up to 3 times

```python
from core.notifications.tasks import send_pending_sms
send_pending_sms.delay()  # Async
# OR
result = send_pending_sms()  # Sync (for testing)
```

### 2. send_pending_emails
- **Schedule:** Every 10 minutes
- **Function:** Send all queued emails
- **Auto-retry:** Failed emails retried up to 3 times

### 3. send_payment_reminder_notifications
- **Schedule:** Daily at 8:00 AM
- **Function:** Send reminders for invoices due in 7 days
- **Condition:** Only if parent opted in + not in quiet hours

```python
# Automatically sends for all invoices with due_date = today + 7 days
# Respects NotificationPreference.payment_reminder setting
```

### 4. send_arrears_notifications
- **Schedule:** Daily at 2:00 PM
- **Function:** Send arrears alerts for overdue fees
- **Levels:**
  - **Warning:** 30-59 days overdue
  - **Critical:** 60+ days overdue

### 5. cleanup_old_notifications
- **Schedule:** Weekly Sunday 3:00 AM
- **Function:** Delete notification logs older than 90 days
- **Purpose:** Keep database lean

## Integration with Finance Engine

### Automatic Notification Triggers

**1. Invoice Issued**
```python
# When: Invoice.status changes to 'issued'
# Event: 'invoice_issued'
# Template: "Invoice {{invoice_number}} (KES {{amount}}) issued"
# Who: Parent of student

# In fees/models.py or views_api.py signal:
from core.notifications.services import NotificationService

notification = NotificationService.create_notification(
    recipient=invoice.student.user,
    event_type='invoice_issued',
    title=f'Invoice {invoice.invoice_number} Issued',
    message=f'An invoice for KES {invoice.total_amount} has been issued',
    student=invoice.student,
    invoice=invoice,
    data={
        'invoice_number': invoice.invoice_number,
        'amount': str(invoice.total_amount),
        'due_date': str(invoice.due_date),
    }
)
NotificationService.dispatch_notification(notification)
```

**2. Payment Received**
```python
# When: Payment.status = 'completed'
# Event: 'payment_received'
# Template: "Payment of KES {{amount}} received for invoice {{invoice_number}}"
# Who: Parent of student
```

**3. Arrears Warning/Critical**
```python
# When: ArrearsService.update_arrears_for_student() runs
# Event: 'arrears_warning' (30-59 days) OR 'arrears_critical' (60+ days)
# Schedule: Daily at 2 PM via Celery
# Template: "Student account has {{days_outstanding}} days overdue fees"
```

## Usage Examples

### Example 1: Send Invoice Issued Notification

```python
# In Finance Engine (when invoice created)
from core.notifications.services import NotificationService

def create_invoice(...):
    invoice = Invoice.objects.create(...)
    
    # Check if parent wants notifications
    parent = invoice.student.user
    if NotificationService.should_notify(parent, 'invoice_issued'):
        notification = NotificationService.create_notification(
            recipient=parent,
            event_type='invoice_issued',
            title=f'Invoice {invoice.invoice_number}',
            message=f'Invoice for KES {invoice.total_amount} issued',
            student=invoice.student,
            invoice=invoice,
            data={...}
        )
        # Queue for sending (SMSTask will pick up)
        NotificationService.dispatch_notification(notification)
```

### Example 2: Manual Bulk SMS

```python
# Manually send SMS to all parents in a school
from core.fees.models import Student
from core.notifications.models import Notification, SMSLog
from core.notifications.services import NotificationService

students = Student.objects.filter(school=school)
for student in students:
    parent = student.user
    notification = NotificationService.create_notification(
        recipient=parent,
        event_type='system_alert',
        title='School Announcement',
        message='School will close on Friday',
        data={}
    )
    NotificationService.dispatch_notification(notification)
```

### Example 3: Parent Disables SMS

```python
# Parent API call
PUT /notifications/api/preferences/
{
    "sms_enabled": false
}

# Now only emails will be sent
# Next payment notification will skip SMS and only send email
```

## Admin Interface

**Features:**
- Color-coded status badges (green=sent, red=failed, blue=queued)
- SMS/Email log viewer with error details
- Parent preference management
- Template editor for multi-language support
- Engagement tracking (email opened/clicked)
- Retry mechanism for failed sends

## Monitoring & Troubleshooting

**Check SMS Queue:**
```bash
python manage.py shell
from core.notifications.models import SMSLog
SMSLog.objects.filter(status='failed').count()  # How many failed
SMSLog.objects.filter(status='queued').count()  # How many waiting
```

**View SMS Errors:**
```bash
failed_sms = SMSLog.objects.filter(status='failed').order_by('-created_at')[:10]
for sms in failed_sms:
    print(f"{sms.phone_number}: {sms.error_message}")
```

**Check Celery Tasks:**
```bash
# Monitor Celery queue
celery -A config worker --loglevel=info

# View beat schedule
celery -A config beat --loglevel=info
```

## Performance Considerations

- SMS/Email delivery is **async** (doesn't block user request)
- Queued notifications batched every 5-10 minutes
- Template rendering cached
- Database indexes on (recipient, is_read) and (status, created_at)
- Old logs cleaned up automatically (90-day retention)

## Security

- Phone numbers encrypted in transit (HTTPS)
- Provider API keys in environment variables (not committed)
- Quiet hours prevent spam (no alerts between 10 PM - 7 AM)
- Recipients can opt-out of any event type
- Email templates sanitized (no XSS)
- SMS message length limited (160 chars SMS, 1000 email)

## Testing

```bash
# Run with test SMS provider
SMS_PROVIDER=test python manage.py shell
from core.notifications.tasks import send_pending_sms
send_pending_sms()  # Will log instead of send

# Send test SMS to yourself
POST /notifications/api/preferences/test_sms/
{"phone_number": "0712345678"}
```

---

**System Philosophy:**
The Notifications Layer is invisible when working - parents receive alerts without friction. But it's mission-critical when problems arise: payment reminders prevent arrears, arrears alerts protect school revenue, and delivery logs ensure accountability. Every notification sent is auditable; every failure is logged and retryable.
