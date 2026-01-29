# Multi-Tenant Architecture Implementation Plan

## Overview
Transform Phase 1 attendance system into a multi-tenant platform supporting multiple schools on one deployment.

**Pattern**: Shared-database with school_id tagging (recommended)
- Single database
- Each record tagged with school_id
- Tenant awareness at every layer
- PWA can store school_id locally

---

## Implementation Strategy

### Layer 1: Core Models (Tenant Foundation)
- ✅ School model (already exists)
- Add tenant filtering to all models
- Create Tenant mixin for reusability
- Update migrations

### Layer 2: API & Permissions
- Filter querysets by tenant
- Permission classes check tenant
- Exclude cross-tenant data

### Layer 3: Frontend
- Login selects school/tenant
- LocalStorage stores school_id
- IndexedDB prefixed by school_id
- API auto-includes school_id

### Layer 4: Sync Engine
- Queue tracks tenant
- Sync respects tenant boundaries
- Offline data per-tenant

---

## Files to Modify

### Backend
1. `backend/core/models.py` - Add Tenant mixin
2. `backend/people/models.py` - Add school FK
3. `backend/attendance/models.py` - Add school FK
4. `backend/core/permissions.py` - Tenant filtering
5. `backend/api/routers.py` - Tenant querysets
6. `backend/config/settings.py` - Middleware

### Frontend
1. `frontend/views/login.html` - School selection
2. `frontend/scripts/auth.js` - Tenant management
3. `frontend/scripts/app.js` - Initialize with tenant
4. `frontend/scripts/db.js` - Add tenant to stores
5. `frontend/scripts/sync.js` - Tenant-aware sync

---

## Phase: Multi-Tenant (1.5)
This extends Phase 1 with enterprise multi-tenant capabilities.
