# Multi-Tenant Quick Reference

## Frontend Integration Checklist

### 1. Initialize on App Load
```javascript
// app.js - Load BEFORE other modules
window.authManager = new TenantAuthManager();
await window.authManager.init();

// Check authentication
if (!window.authManager.isAuthenticated()) {
  window.location.href = '/login.html';
}

// Initialize other managers
window.db = new IndexedDBManager();
window.syncManager = new SyncManager();
```

### 2. Use School Context in Controllers
```javascript
class AttendanceController {
  constructor() {
    this.authManager = window.authManager;
    this.schoolId = this.authManager.getSchoolId();
  }

  async loadData() {
    // Option 1: Use APIheaders (auto-includes Bearer token)
    const headers = this.authManager.getHeaders();
    const response = await fetch('/api/v1/attendance/sessions/', {
      headers
    });

    // Option 2: Fetch interceptors auto-inject (preferred)
    const response = await fetch('/api/v1/attendance/sessions/');
  }

  async saveData() {
    // All saved records auto-get schoolId
    await db.saveAttendanceRecord({
      sessionId: '123',
      studentId: 45,
      status: 'P'
      // schoolId automatically added
    });
  }
}
```

### 3. Get School Data (Filtered)
```javascript
// Get all sessions for current school (auto-filtered)
const sessions = await db.getAllFromStore('attendanceSessions');

// Get specific school data (explicit)
const sessions = await db.getForSchool('attendanceSessions');

// Clear school data on logout
await db.clearForSchool('syncQueue');
```

### 4. Queue Syncs with School Context
```javascript
// Sync queue automatically includes schoolId
syncManager.queueChange('attendance_batch', {
  sessionId: '123',
  records: {...}
  // schoolId automatically added
});

// Only current school syncs on pending
await syncManager.syncPending();
```

---

## Backend Integration Checklist

### 1. Apply Tenant Mixins to Models
```python
from core.tenants import TenantMixin

class AttendanceSession(TenantMixin, models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_index=True)
    date = models.DateField()
    # ... other fields
    
# Usage:
sessions = AttendanceSession.objects.for_school(school_id)
```

### 2. Apply Tenant Isolation to ViewSets
```python
from core.tenant_permissions import TenantIsolationMixin, IsTenantMember

class AttendanceSessionViewSet(TenantIsolationMixin, viewsets.ModelViewSet):
    permission_classes = [IsTenantMember]
    
    # TenantIsolationMixin handles:
    # - Filtering queryset by user.school
    # - Setting school on create
    # - Validating tenant membership
```

### 3. Query Models Using School Context
```python
# From user:
user_school = request.user.school
sessions = AttendanceSession.objects.filter(school=user_school)

# Or use manager method:
sessions = AttendanceSession.objects.for_school(user_school.id)

# Or auto-filter via TenantIsolationMixin:
# (ViewSet automatically does this)
```

### 4. Create Resources with School Context
```python
# In serializer's create/update:
def create(self, validated_data):
    # Option 1: TenantIsolationMixin sets it automatically
    # Option 2: Set explicitly
    validated_data['school'] = self.context['request'].user.school
    return super().create(validated_data)
```

---

## Adding Tenant Support to New Models

### Step 1: Add School FK
```python
class MyNewModel(TenantMixin, models.Model):
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        db_index=True
    )
    # ... your fields
    
    class Meta:
        # Add compound indexes
        indexes = [
            models.Index(fields=['school', 'date']),
        ]
```

### Step 2: Create Serializer
```python
class MyNewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyNewModel
        fields = ['id', 'school', ...]
    
    def create(self, validated_data):
        validated_data['school'] = self.context['request'].user.school
        return super().create(validated_data)
```

### Step 3: Create ViewSet
```python
from core.tenant_permissions import TenantIsolationMixin, IsTenantMember

class MyNewViewSet(TenantIsolationMixin, viewsets.ModelViewSet):
    serializer_class = MyNewSerializer
    permission_classes = [IsTenantMember]
    
    # TenantIsolationMixin provides get_queryset()
    # and handles school filtering automatically
```

### Step 4: Update Frontend
```javascript
// In controller:
async loadData() {
  const data = await db.getForSchool('myNewStore');
  return data;
}

async saveData(record) {
  await db.addToStore('myNewStore', {
    ...record,
    schoolId: this.authManager.getSchoolId()
  });
}
```

---

## Common Patterns

### Pattern 1: List Resources (Current School Only)
**Backend:**
```python
class AttendanceViewSet(TenantIsolationMixin, viewsets.ModelViewSet):
    # TenantIsolationMixin.get_queryset() returns:
    # Attendance.objects.filter(school=request.user.school)
    pass
```

**Frontend:**
```javascript
async loadAttendance() {
  const headers = this.authManager.getHeaders();
  const response = await fetch('/api/v1/attendance/', { headers });
  // Returns only current school's attendance
}
```

### Pattern 2: Create Resource (Auto-Assign School)
**Backend:**
```python
class AttendanceSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data['school'] = self.context['request'].user.school
        return Attendance.objects.create(**validated_data)
```

**Frontend:**
```javascript
async saveAttendance(record) {
  // Don't need to set school_id - server does it
  const response = await fetch('/api/v1/attendance/', {
    method: 'POST',
    headers: this.authManager.getHeaders(),
    body: JSON.stringify(record)
  });
}
```

### Pattern 3: Filter by School (Frontend)
```javascript
// Get all records for current school
const sessions = await db.getForSchool('attendanceSessions');

// Get all records (auto-filtered by school)
const allSessions = await db.getAllFromStore('attendanceSessions');

// Clear school-specific data
await db.clearForSchool('syncQueue');
```

### Pattern 4: Multi-School Admin View (Future)
**Backend:**
```python
class AdminViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminOfSchool]
    
    def list(self, request):
        if request.user.is_superadmin:
            # Superadmin sees all schools
            queryset = School.objects.all()
        else:
            # Admin sees only their schools
            queryset = request.user.managed_schools.all()
        # ...
```

---

## Debugging Tips

### 1. Check School Context
```javascript
// Frontend:
console.log('School:', window.authManager.getSchoolId());
console.log('School Code:', window.authManager.getSchoolCode());
console.log('Headers:', window.authManager.getHeaders());
```

### 2. Verify IndexedDB Records
```javascript
// Check if records have schoolId
const records = await db.getAllFromStore('attendanceSessions');
records.forEach(r => console.log(r.schoolId, r.id));

// Check sync queue
const queue = await db.getAllFromStore('syncQueue');
queue.forEach(q => console.log('School:', q.schoolId, 'Action:', q.action));
```

### 3. Verify API Requests
```javascript
// Check headers are sent
const headers = window.authManager.getHeaders();
console.log('Authorization:', headers['Authorization']);

// Check response filtering
fetch('/api/v1/attendance/sessions/').then(r => r.json()).then(data => {
  console.log('Returned sessions:', data.length);
  data.forEach(s => console.log('Session school:', s.school));
});
```

### 4. Backend Verification
```python
# Django shell:
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='teacher1')
>>> print(f"User school: {user.school}")
>>> from attendance.models import Attendance
>>> Attendance.objects.filter(school=user.school).count()
# Should return only this school's records
```

---

## Deployment Checklist

- [ ] All models have `school` FK
- [ ] All viewsets use TenantIsolationMixin
- [ ] All serializers set `school` on create
- [ ] Frontend loads auth.js before other scripts
- [ ] Login page configured in app
- [ ] IndexedDB stores include schoolId
- [ ] Sync queue respects schoolId
- [ ] Controllers use authManager.getHeaders()
- [ ] Database migrations applied
- [ ] Indexes created for school + date queries
- [ ] Test with 2+ schools
- [ ] Verify data isolation between schools
- [ ] Offline sync works per school
- [ ] Token refresh works correctly

---

## API Reference

### Auth Endpoints
```
POST /api/v1/auth/school-login/
  { school_code, username, password }
  → { access_token, refresh_token, school, user }

GET /api/v1/auth/schools/
  → List of schools user can access

POST /api/v1/auth/switch-school/
  { school_id }
  → { access_token, refresh_token, school, user }

GET /api/v1/auth/current-school/
  → { school, user }

POST /api/v1/auth/logout/
  → { success: true }
```

### Protected Endpoints (Auto-Filtered by School)
```
GET /api/v1/attendance/sessions/
  → List only current school's sessions

POST /api/v1/attendance/records/
  → Create record for current school (school auto-set)

GET /api/v1/classes/
  → List only current school's classes

GET /api/v1/students/
  → List only current school's students
```

---

## Tenant Context Flow

```
┌─────────────────┐
│  User Logs In   │
│  (school_code)  │
└────────┬────────┘
         │
    ┌────▼────────────┐
    │ Backend         │
    │ Resolves School │
    │ Issues JWT      │
    └────┬────────────┘
         │
    ┌────▼──────────────────┐
    │ Frontend              │
    │ Stores school_id      │
    │ Loads auth.js         │
    │ Setup interceptors    │
    └────┬──────────────────┘
         │
    ┌────▼────────────────────┐
    │ API Request             │
    │ Auto-inject auth header │
    │ Fetch interceptor acts  │
    └────┬────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Backend                   │
    │ Validate JWT              │
    │ Extract user.school       │
    │ TenantIsolationMixin      │
    │ Filter by user.school     │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Database                  │
    │ Query school-filtered     │
    │ Return school's data only │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Frontend                  │
    │ Save to IndexedDB         │
    │ Auto-tag with schoolId    │
    │ Display to user           │
    └──────────────────────────┘
```

---

## Multi-School User Admin

```javascript
// Admin switching schools:
class AdminPanel {
  async switchSchool(schoolId) {
    // Call backend endpoint
    const response = await fetch('/api/v1/auth/switch-school/', {
      method: 'POST',
      headers: window.authManager.getHeaders(),
      body: JSON.stringify({ school_id: schoolId })
    });
    
    const data = await response.json();
    
    // Update local context
    window.authManager.storeAuth(data);
    
    // Reload app for new school
    location.reload();
  }
}
```

---

Generated: Multi-Tenant Implementation
Ready for: Production Deployment
Supports: ∞ Schools in Single Deployment
