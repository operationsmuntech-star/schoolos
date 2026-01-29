# Multi-Tenant Setup & Initialization Guide

## 🚀 Quick Start: Setting Up Multi-Tenant System

---

## Phase 1: Backend Setup (Django)

### Step 1: Apply Multi-Tenant Infrastructure

1. **Register Tenant Apps** in `settings.py`:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'core',      # Add tenant infrastructure
    'attendance',
    'people',
]
```

2. **Configure Middleware** in `settings.py`:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'core.tenants.TenantMiddleware',  # Add this
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
```

3. **Verify Models Have School FK**:
```bash
# Check core/models.py
python manage.py shell
>>> from core.models import School, AttendanceSession
>>> AttendanceSession._meta.fields
# Should show: <ForeignKey: school> field
```

### Step 2: Run Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create initial school
python manage.py shell
>>> from core.models import School
>>> School.objects.create(code='DEMO', name='Demo School')
```

### Step 3: Create Test Data

Create `backend/management/commands/create_test_schools.py`:

```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import School, Class, Subject
from people.models import Teacher

class Command(BaseCommand):
    help = 'Create test schools with sample data'

    def handle(self, *args, **options):
        # School 1
        school1 = School.objects.create(
            code='SCHOOL_A',
            name='School A',
            email='admin@schoola.com'
        )
        self.stdout.write(f'✓ Created {school1.name}')

        # Create users for School 1
        user1 = User.objects.create_user(
            username='teacher_a',
            password='demo123',
            email='teacher@schoola.com'
        )
        Teacher.objects.create(
            user=user1,
            school=school1,
            employee_id='T001'
        )

        # School 2
        school2 = School.objects.create(
            code='SCHOOL_B',
            name='School B',
            email='admin@schoolb.com'
        )
        self.stdout.write(f'✓ Created {school2.name}')

        # Create users for School 2
        user2 = User.objects.create_user(
            username='teacher_b',
            password='demo123',
            email='teacher@schoolb.com'
        )
        Teacher.objects.create(
            user=user2,
            school=school2,
            employee_id='T002'
        )

        self.stdout.write(self.style.SUCCESS('✓ Test data created'))
```

Run it:
```bash
python manage.py create_test_schools
```

### Step 4: Configure JWT Settings

In `settings.py`:
```python
# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

### Step 5: Register Auth Endpoints

In `backend/urls.py`:
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import SchoolViewSet
from api.auth import (
    SchoolLoginView,
    GetSchoolsView,
    SwitchSchoolView,
    CurrentSchoolView,
    LogoutView
)

router = DefaultRouter()
router.register(r'schools', SchoolViewSet)

urlpatterns = [
    path('api/v1/auth/school-login/', SchoolLoginView.as_view(), name='school-login'),
    path('api/v1/auth/schools/', GetSchoolsView.as_view(), name='get-schools'),
    path('api/v1/auth/switch-school/', SwitchSchoolView.as_view(), name='switch-school'),
    path('api/v1/auth/current-school/', CurrentSchoolView.as_view(), name='current-school'),
    path('api/v1/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/v1/', include(router.urls)),
]
```

### Step 6: Enable CORS for Frontend

In `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True
```

### Step 7: Test Backend Endpoints

```bash
# Start server
python manage.py runserver

# Test school login
curl -X POST http://localhost:8000/api/v1/auth/school-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "school_code": "SCHOOL_A",
    "username": "teacher_a",
    "password": "demo123"
  }'

# Response should include:
# {
#   "access_token": "eyJhbGc...",
#   "refresh_token": "eyJhbGc...",
#   "school": {"id": 1, "code": "SCHOOL_A", "name": "School A"},
#   "user": {"id": 1, "username": "teacher_a", ...}
# }
```

---

## Phase 2: Frontend Setup

### Step 1: Prepare Frontend Structure

Ensure files exist:
```
frontend/
├── views/
│   ├── login.html          ← Multi-tenant login page
│   ├── attendance.html     ← Main app (check for auth)
│   └── index.html          ← App shell
├── scripts/
│   ├── auth.js             ← TenantAuthManager
│   ├── db.js               ← IndexedDB (school-aware)
│   ├── sync.js             ← SyncManager (school-aware)
│   ├── attendance-controller.js ← Multi-tenant aware
│   └── app.js              ← Initialize authManager
├── styles/
│   └── tailwind.css        ← Styling
└── manifest.json           ← PWA manifest
```

### Step 2: Update index.html Entry Point

In `frontend/views/index.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>School Attendance System</title>
    <link rel="stylesheet" href="../styles/tailwind.css">
    <link rel="manifest" href="../manifest.json">
</head>
<body class="bg-gray-50">
    <div id="app"></div>

    <!-- Core dependencies (ORDER MATTERS) -->
    <script src="../scripts/auth.js"></script>      <!-- Must load first -->
    <script src="../scripts/db.js"></script>        <!-- IndexedDB -->
    <script src="../scripts/sync.js"></script>      <!-- Sync engine -->
    
    <!-- App initialization -->
    <script src="../scripts/app.js"></script>       <!-- Initializes all -->
    <script src="../scripts/attendance-controller.js"></script>
</body>
</html>
```

### Step 3: Create/Update app.js

In `frontend/scripts/app.js`:
```javascript
/**
 * Application Entry Point
 * Initializes multi-tenant system
 */

// Step 1: Initialize and load auth (MUST BE FIRST)
window.authManager = new TenantAuthManager('http://localhost:8000/api/v1');

async function initializeApp() {
  try {
    console.log('Initializing application...');
    
    // Step 2: Initialize auth manager
    await window.authManager.init();
    console.log('✓ Auth manager initialized');
    
    // Step 3: Check authentication
    if (!window.authManager.isAuthenticated()) {
      console.log('⚠ User not authenticated, redirecting to login');
      window.location.href = './login.html';
      return;
    }
    
    console.log('✓ User authenticated:', window.authManager.getTenantContext());
    
    // Step 4: Initialize IndexedDB
    window.db = new IndexedDBManager();
    await window.db.init();
    console.log('✓ IndexedDB initialized');
    
    // Step 5: Initialize SyncManager
    window.syncManager = new SyncManager();
    console.log('✓ SyncManager initialized');
    
    // Step 6: Initialize AttendanceController
    window.attendanceController = new AttendanceController();
    console.log('✓ AttendanceController initialized');
    
    // Step 7: Display school context
    const context = window.authManager.getTenantContext();
    displaySchoolInfo(context);
    
    console.log('✅ Application fully initialized');
    
  } catch (error) {
    console.error('❌ Initialization error:', error);
    document.body.innerHTML = `
      <div class="p-4 bg-red-100 text-red-800 rounded">
        <h1 class="font-bold">Initialization Error</h1>
        <p>${error.message}</p>
        <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-red-600 text-white rounded">
          Retry
        </button>
      </div>
    `;
  }
}

function displaySchoolInfo(context) {
  const schoolDiv = document.getElementById('schoolInfo') || createSchoolDiv();
  schoolDiv.innerHTML = `
    <div class="p-4 bg-blue-50 border border-blue-200 rounded">
      <h2 class="font-bold">School: ${context.school.name}</h2>
      <p class="text-sm text-gray-600">Code: ${context.school.code}</p>
      <p class="text-sm text-gray-600">User: ${context.user.username}</p>
    </div>
  `;
}

function createSchoolDiv() {
  const div = document.createElement('div');
  div.id = 'schoolInfo';
  div.style.position = 'fixed';
  div.style.top = '10px';
  div.style.right = '10px';
  div.style.zIndex = '1000';
  document.body.appendChild(div);
  return div;
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}

// Optional: Refresh token before expiry
setInterval(async () => {
  try {
    await window.authManager.refreshAccessToken();
  } catch (e) {
    console.warn('Token refresh failed:', e);
  }
}, 50 * 60 * 1000); // Every 50 minutes (before 1 hour expiry)
```

### Step 4: Verify login.html Exists

Check that `frontend/views/login.html` is properly set up (should already exist from Phase 2).

### Step 5: Update attendance.html

In `frontend/views/attendance.html`, ensure it includes:
```html
<!-- Authentication check -->
<script>
  // Redirect if not authenticated
  if (!window.authManager?.isAuthenticated()) {
    window.location.href = './login.html';
  }
</script>
```

### Step 6: Configure API Endpoint

In `frontend/scripts/auth.js`, ensure API base is correct:
```javascript
class TenantAuthManager {
  constructor(apiBase = '/api/v1') {
    this.apiBase = apiBase;
    // For development: http://localhost:8000/api/v1
    // For production: /api/v1 (relative to same domain)
  }
}
```

### Step 7: Test Frontend

```bash
# Start frontend dev server
cd frontend
python -m http.server 8001

# Open browser
# http://localhost:8001/views/login.html

# Test login with credentials:
# School Code: SCHOOL_A
# Username: teacher_a
# Password: demo123
```

---

## Phase 3: Integration Testing

### Test 1: Multi-School Data Isolation

```javascript
// Browser console after logging in as teacher_a (SCHOOL_A)

// Verify school context
window.authManager.getSchoolId()  // Should return 1
window.authManager.getSchoolCode()  // Should return "SCHOOL_A"

// Verify token is present
const headers = window.authManager.getHeaders()
console.log(headers['Authorization'])  // Should have Bearer token

// Load attendance data
const sessions = await db.getAllFromStore('attendanceSessions')
console.log('Sessions for SCHOOL_A:', sessions)
// Should show only School A sessions

// Logout and login as teacher_b (SCHOOL_B)
// Repeat above - should see only SCHOOL_B data
```

### Test 2: Offline Sync

```javascript
// With teacher_a (SCHOOL_A) logged in:

// 1. Mark attendance offline
await db.saveAttendanceRecord({
  sessionId: 'sess_1',
  studentId: 10,
  status: 'P'
})

// 2. Check queue
const queue = await db.getAllFromStore('syncQueue')
console.log('Queue:', queue)
// Should show record with schoolId=1

// 3. Go online and sync
await window.syncManager.syncPending()

// 4. Check server
// Should see new Attendance record for SCHOOL_A
```

### Test 3: Admin School Switching

```javascript
// If user has multiple schools:

// 1. Get available schools
const schools = await window.authManager.getAvailableSchools()
console.log('Available schools:', schools)

// 2. Switch to another school (admin only)
await window.authManager.switchSchool(2)

// 3. Verify new context
window.authManager.getSchoolId()  // Should return 2

// 4. Load new school's data
const sessions = await db.getAllFromStore('attendanceSessions')
// Should show SCHOOL_B data
```

---

## Phase 4: Deployment

### Development Environment
```bash
# Terminal 1: Run Django
cd backend
python manage.py runserver

# Terminal 2: Run Frontend (optional)
cd frontend
python -m http.server 8001
```

### Production Deployment

1. **Build Frontend**
```bash
# Minify and bundle (if using build tool)
# Or serve static files as-is with web server
```

2. **Deploy Django**
```bash
# Using Gunicorn + Nginx
gunicorn backend.wsgi:application --bind 0.0.0.0:8000

# Or using Docker
docker build -t school-api .
docker run -p 8000:8000 school-api
```

3. **Configure Nginx**
```nginx
server {
    listen 80;
    server_name app.schoolattendance.com;

    # Static files
    location /static/ {
        alias /app/static/;
    }

    # Frontend
    location / {
        root /app/frontend;
        try_files $uri /views/index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. **Database**
```bash
# Migrate to PostgreSQL in production
# Update settings.py with prod credentials

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'school_attendance_prod',
        'USER': 'postgres',
        'PASSWORD': 'secure_password',
        'HOST': 'db.example.com',
        'PORT': '5432',
    }
}
```

---

## ✅ Verification Checklist

- [ ] Django migrations applied
- [ ] Test schools created
- [ ] Auth endpoints working
- [ ] Frontend auth.js loaded
- [ ] Login page functional
- [ ] Multi-school data isolation verified
- [ ] Offline sync working per school
- [ ] Admin school switching functional (if applicable)
- [ ] CORS configured correctly
- [ ] JWT tokens valid and refreshing
- [ ] IndexedDB school-tagged records
- [ ] SyncQueue school-filtered
- [ ] Production database configured
- [ ] Nginx/Web server configured
- [ ] SSL certificate installed (production)
- [ ] Backup strategy in place
- [ ] Monitoring set up

---

## 🐛 Debugging

### Backend Issues

**Problem: "School not found" error on login**
```python
# Check school exists
python manage.py shell
>>> from core.models import School
>>> School.objects.filter(code='SCHOOL_A').exists()
```

**Problem: User not associated with school**
```python
>>> from django.contrib.auth.models import User
>>> from people.models import Teacher
>>> user = User.objects.get(username='teacher_a')
>>> user.teacher.school  # Should not be None
```

**Problem: API returns 403 Forbidden**
```python
# Verify TenantIsolationMixin is applied
# Check IsTenantMember permission is in place
# Verify user.school is set
```

### Frontend Issues

**Problem: Login stuck on loading**
```javascript
// Check API endpoint is correct
console.log(window.authManager.apiBase)

// Check for CORS errors in console
// Ensure Django CORS_ALLOWED_ORIGINS configured
```

**Problem: Blank page after login**
```javascript
// Check app.js initialization
console.log('authManager:', window.authManager.isAuthenticated())
console.log('db:', window.db)
console.log('syncManager:', window.syncManager)
```

**Problem: No data visible**
```javascript
// Check school context
console.log('School ID:', window.authManager.getSchoolId())

// Check IndexedDB has data
const sessions = await db.getAllFromStore('attendanceSessions')
console.log('Sessions:', sessions)
```

---

## 📞 Support Resources

**Documentation Files:**
- `MULTI_TENANT_IMPLEMENTATION.md` - Complete architecture
- `MULTI_TENANT_QUICK_REFERENCE.md` - Developer quick reference
- `MULTI_TENANT_SUMMARY.md` - Overview and status

**Key Files to Review:**
- `backend/core/tenants.py` - Tenant infrastructure
- `backend/core/tenant_permissions.py` - Permission system
- `backend/api/auth.py` - Auth endpoints
- `frontend/scripts/auth.js` - Frontend auth manager

---

## 🎉 Success!

When you see:
```
✅ Application fully initialized
✓ Auth manager initialized
✓ IndexedDB initialized
✓ SyncManager initialized
✓ AttendanceController initialized
```

And you can:
- Login with different school codes
- See different data per school
- Work offline and sync per school
- Switch schools (if admin)

**You have successfully implemented multi-tenant architecture!** 🚀
