# Offline-First Architecture

## How It Works

### Layer 1: Local IndexedDB
```
Browser (offline)
    ↓
IndexedDB (offline storage)
    ├── students (synced)
    ├── teachers (synced)
    ├── attendance (local-first)
    └── sync_queue (pending changes)
```

### Layer 2: Service Worker
- Intercepts all network requests
- Returns cached responses if offline
- Queues failed requests

### Layer 3: Sync Engine
When online, sync queue to server:
```
Local changes → Sync Engine → Django API → SQLite
                    ↓
            Conflict Resolution → Last write wins
```

## Data Flows

### Creating Attendance Record (Offline)

```
1. User marks attendance offline
   ↓
2. IndexedDB stores locally (instant)
   ↓
3. Added to sync_queue
   ↓
4. Service Worker caches response
   ↓
5. UI updates immediately (optimistic)
```

### Syncing When Online

```
1. Browser detects online
   ↓
2. SyncManager.syncPending()
   ↓
3. Batch POST to /api/v1/sync/
   ↓
4. Server processes with conflict resolution
   ↓
5. Clear sync_queue
   ↓
6. Update local cache
```

## Conflict Resolution

### Last-Write-Wins (LWW)
Default strategy:
- If same record edited on multiple devices
- Server keeps record with latest timestamp
- Looser's changes discarded

```javascript
if (clientRecord.marked_at > serverRecord.marked_at) {
  use clientRecord;
} else {
  use serverRecord;
}
```

### Future: Custom Resolution
Schools can define:
- "Teacher wins over student"
- "School admin approval required"
- "Custom merge logic"

## Storage Quotas

### IndexedDB Quotas
- Chrome: 50% of disk space
- Safari: 50GB per domain
- Firefox: 10GB per domain

For typical school:
- 1000 students
- 100 teachers
- 2 terms of attendance
- ≈ 50-100MB

Safe under any quota.

## Caching Strategy

### Service Worker Cache

```javascript
// On install: cache app shell
urlsToCache = [
  '/',
  '/styles/tailwind.css',
  '/scripts/app.js',
  '/views/dashboard.html',
  '/offline.html'
]

// On fetch:
if (request in cache) return cache;
else try network;
else return offline.html;
```

### Cache Busting
```
service-worker-v1.js
service-worker-v2.js
// On update, old cache deleted
```

## Sync Queue Structure

```json
{
  "id": 123,
  "user_id": 456,
  "action": "update",
  "data_type": "attendance",
  "record_id": "attendance_789",
  "payload": {
    "status": "P",
    "marked_at": "2026-01-29T10:30:00Z",
    "remarks": "Present"
  },
  "created_at": "2026-01-29T10:29:00Z",
  "synced": false
}
```

## Network Detection

```javascript
// Online detection
window.addEventListener('online', () => syncManager.syncPending());
window.addEventListener('offline', () => console.log('offline'));

// Manual check
if (navigator.onLine) { /* sync */ }
```

## Best Practices

✅ **DO**
- Store small, self-contained records
- Use IDs for relationships
- Serialize dates as ISO 8601
- Batch sync on reconnection

❌ **DON'T**
- Store entire Student object in Attendance
- Use nested objects (breaks indexing)
- Sync large files (>10MB)
- Block UI during sync

## Testing Offline

### Chrome DevTools
1. Open DevTools
2. Go to "Network" tab
3. Check "Offline"
4. Interact with app
5. Go back online
6. Watch sync happen

### Service Worker Debugging
- DevTools → Application → Service Workers
- Check "Offline" to simulate

## Limitations

- ❌ Real-time collaboration (use WebSocket for Phase 2)
- ❌ Large file uploads (use signed URLs for Phase 2)
- ❌ Cross-device sync (device is primary)
- ⚠️ Conflicts resolved automatically (log for admin review)

---

**Offline-first means the network is optional, not required.**
