/**
 * Sync Logic - Phase 1 Complete Offline-First Sync Engine
 */

class SyncManager {
  constructor() {
    this.apiBase = '/api/v1';
    this.isOnline = navigator.onLine;
    this.syncQueue = [];
    this.isSyncing = false;
    this.lastSyncTime = null;
    this.maxRetries = 3;
    this.retryDelays = [1000, 5000, 10000]; // ms
    this.init();
  }

  init() {
    console.log('🔄 SyncManager initialized');
    
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
    
    // Auto-sync every 5 minutes if online
    setInterval(() => this.autoSync(), 5 * 60 * 1000);
  }

  handleOnline() {
    this.isOnline = true;
    console.log('🟢 Online - starting sync');
    this.updateSyncIndicator();
    this.syncPending();
  }

  handleOffline() {
    this.isOnline = false;
    console.log('🔴 Offline - queuing changes');
    this.updateSyncIndicator();
  }

  queueChange(action, data) {
    """Queue a change for sync"""
    const change = {
      id: this.generateId(),
      action,
      data,
      timestamp: new Date().toISOString(),
      retryCount: 0,
      status: 'pending',
      schoolId: this.getSchoolId()
    };

    this.syncQueue.push(change);
    console.log(`📝 Queued: ${action}`, change);
    
    // Persist to IndexedDB
    db.addToStore('syncQueue', change).catch(e => console.error('Queue storage error:', e));
    
    this.updateSyncIndicator();
  }

  async autoSync() {
    """Automatic sync if online"""
    if (this.isOnline && !this.isSyncing) {
      await this.syncPending();
    }
  }

  async syncPending() {
    """Sync all pending changes for current school"""
    if (this.isSyncing || this.syncQueue.length === 0) {
      return;
    }

    this.isSyncing = true;
    this.updateSyncIndicator();
    
    const currentSchoolId = this.getSchoolId();
    const queue = this.syncQueue.filter(item => item.schoolId === currentSchoolId);
    
    console.log(`🔄 Starting sync of ${queue.length} changes for school ${currentSchoolId}`);

    const errors = [];

    for (const item of queue) {
      try {
        const success = await this.syncItem(item);
        if (success) {
          // Remove from queue
          this.syncQueue = this.syncQueue.filter(i => i.id !== item.id);
          await db.deleteFromStore('syncQueue', item.id);
          console.log(`✓ Synced: ${item.action}`);
        } else {
          item.retryCount++;
          if (item.retryCount >= this.maxRetries) {
            errors.push(item);
            this.syncQueue = this.syncQueue.filter(i => i.id !== item.id);
          }
        }
      } catch (error) {
        console.error('Sync error:', error);
        item.retryCount++;
        errors.push(error);
      }
    }

    this.isSyncing = false;
    this.lastSyncTime = new Date();
    this.updateSyncIndicator();

    if (errors.length === 0) {
      console.log('✓ All items synced');
      this.notify('Sync complete', 'success');
    } else {
      console.warn(`⚠️ ${errors.length} items failed to sync`);
      this.notify(`Sync: ${this.syncQueue.length} pending`, 'warning');
    }
  }

  async syncItem(item, retryCount = 0) {
    """Sync individual item"""
    try {
      let response;

      switch (item.action) {
        case 'attendance_batch':
          response = await this.syncAttendanceBatch(item.data);
          break;
        case 'attendance_single':
          response = await this.syncAttendanceRecord(item.data);
          break;
        case 'exception':
          response = await this.syncException(item.data);
          break;
        default:
          console.warn('Unknown action:', item.action);
          return false;
      }

      if (response.ok) {
        item.status = 'synced';
        return true;
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      if (retryCount < this.maxRetries && !navigator.onLine) {
        // Retry with exponential backoff
        const delay = this.retryDelays[retryCount] || 10000;
        setTimeout(() => this.syncItem(item, retryCount + 1), delay);
        return false;
      }
      throw error;
    }
  }

  async syncAttendanceBatch(data) {
    """Sync batch of attendance records"""
    const records = Object.entries(data.records || {}).map(([studentId, record]) => ({
      student_id: parseInt(studentId),
      status: record.status,
      remarks: record.remarks,
      marked_at: new Date().toISOString()
    }));

    return fetch(`${this.apiBase}/attendance/records/sync_batch/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        session_id: data.sessionId,
        records
      })
    });
  }

  async syncAttendanceRecord(data) {
    """Sync single attendance record"""
    return fetch(`${this.apiBase}/attendance/records/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        session: data.sessionId,
        student_id: data.studentId,
        status: data.status,
        remarks: data.remarks
      })
    });
  }

  async syncException(data) {
    """Sync attendance exception"""
    return fetch(`${this.apiBase}/attendance/exceptions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(data)
    });
  }

  async handleConflict(localRecord, serverRecord) {
    """Handle sync conflicts - last write wins"""
    const localTime = new Date(localRecord.marked_at);
    const serverTime = new Date(serverRecord.marked_at);

    if (localTime > serverTime) {
      console.log('Local record wins (newer)', localRecord);
      return localRecord;
    } else {
      console.log('Server record wins (newer)', serverRecord);
      return serverRecord;
    }
  }

  async getPendingSyncCount() {
    """Get count of pending changes"""
    try {
      const items = await db.getAllFromStore('syncQueue');
      return items.filter(i => i.status === 'pending').length;
    } catch {
      return this.syncQueue.filter(i => i.status === 'pending').length;
    }
  }

  updateSyncIndicator() {
    """Update UI sync status"""
    const status = document.getElementById('syncStatus');
    if (!status) return;

    if (this.isSyncing) {
      status.textContent = '⏳ Syncing...';
      status.className = 'text-sm px-3 py-1 rounded bg-blue-100 text-blue-800';
    } else if (this.syncQueue.length > 0) {
      status.textContent = `📝 ${this.syncQueue.length} pending`;
      status.className = 'text-sm px-3 py-1 rounded bg-yellow-100 text-yellow-800';
    } else if (this.isOnline) {
      status.textContent = '✓ Synced';
      status.className = 'text-sm px-3 py-1 rounded bg-green-100 text-green-800';
    } else {
      status.textContent = '🔴 Offline';
      status.className = 'text-sm px-3 py-1 rounded bg-red-100 text-red-800';
    }
  }

  notify(message, type = 'info') {
    """Show notification"""
    const colors = {
      success: 'bg-green-500',
      error: 'bg-red-500',
      warning: 'bg-yellow-500',
      info: 'bg-blue-500'
    };

    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-3 rounded-lg shadow-lg text-white text-sm z-50 ${colors[type]}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.remove(), 3000);
  }

  generateId() {
    """Generate unique ID"""
    return `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async clear() {
    """Clear sync queue"""
    this.syncQueue = [];
    try {
      await db.clearStore('syncQueue');
    } catch (e) {
      console.error('Error clearing queue:', e);
    }
  }

  async getStatus() {
    """Get full sync status"""
    return {
      isOnline: this.isOnline,
      isSyncing: this.isSyncing,
      pendingCount: this.syncQueue.length,
      lastSyncTime: this.lastSyncTime,
      queue: this.syncQueue
    };
  }

  getSchoolId() {
    """Get current school ID from auth manager"""
    try {
      return window.authManager?.getSchoolId() || null;
    } catch (e) {
      console.warn('Could not get school ID:', e);
      return null;
    }
  }
}

// Initialize sync manager globally
window.syncManager = new SyncManager();
