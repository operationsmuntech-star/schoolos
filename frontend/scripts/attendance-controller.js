/**
 * Attendance Controller - Phase 1 Complete
 * Handles marking attendance, offline storage, and full sync integration
 * Multi-tenant aware with school_id support
 */

class AttendanceController {
  constructor() {
    this.apiBase = '/api/v1';
    this.currentSession = null;
    this.attendanceRecords = {};
    this.students = [];
    this.syncManager = window.syncManager;
    this.authManager = window.authManager;
    this.init();
  }

  init() {
    // Check authentication first
    if (!this.authManager?.isAuthenticated()) {
      this.authManager?.redirectIfNotAuthenticated();
      return;
    }
    
    // Set today's date as default
    const dateInput = document.getElementById('attendanceDate') || document.getElementById('dateInput');
    if (dateInput) dateInput.valueAsDate = new Date();
    
    // Event listeners
    document.getElementById('loadSessionBtn')?.addEventListener('click', () => this.loadSession());
    document.getElementById('saveSessionBtn')?.addEventListener('click', () => this.saveAttendance());
    document.getElementById('closeSessionBtn')?.addEventListener('click', () => this.closeSession());
    document.getElementById('markAllPresentBtn')?.addEventListener('click', () => this.markAllPresent());
    document.getElementById('resetBtn')?.addEventListener('click', () => this.resetForm());
    document.getElementById('classSelect')?.addEventListener('change', () => this.onClassChange());
    document.getElementById('studentFilter')?.addEventListener('input', (e) => this.filterStudents(e.target.value));
    document.getElementById('exportBtn')?.addEventListener('click', () => this.exportAsCSV());
    
    // Load classes on init
    this.loadClasses();
    
    // Monitor online/offline and sync status
    window.addEventListener('online', () => {
      this.updateSyncStatus();
      this.syncManager.syncPending();
    });
    window.addEventListener('offline', () => this.updateSyncStatus());
    
    // Update sync status every 5 seconds
    setInterval(() => this.updateSyncStatus(), 5000);
    
    this.updateSyncStatus();
  }

  async loadClasses() {
    try {
      // In Phase 2, fetch from API
      // For now, load from IndexedDB
      const classes = await db.getAllFromStore('classes');
      const classSelect = document.getElementById('classSelect');
      
      classes.forEach(klass => {
        const option = document.createElement('option');
        option.value = klass.id;
        option.textContent = klass.name;
        classSelect.appendChild(option);
      });
    } catch (error) {
      console.error('Error loading classes:', error);
      this.showMessage('Error loading classes', 'error');
    }
  }

  async onClassChange() {
    const classId = document.getElementById('classSelect').value;
    if (classId) {
      try {
        // Load students for class from IndexedDB
        const students = await db.getFromStore('students', { current_class: parseInt(classId) });
        this.students = students;
      } catch (error) {
        console.error('Error loading students:', error);
      }
    }
  }

  async loadSession() {
    const classId = document.getElementById('classSelect').value;
    const date = document.getElementById('attendanceDate').value;
    const subjectId = document.getElementById('subjectSelect').value;

    if (!classId || !date) {
      this.showMessage('Please select class and date', 'warning');
      return;
    }

    try {
      // Try to fetch from API first (if online)
      if (navigator.onLine) {
        const headers = this.authManager?.getHeaders() || {};
        const response = await fetch(`${this.apiBase}/attendance/sessions/?class_id=${classId}&date=${date}`, {
          headers
        });
        if (response.ok) {
          const sessions = await response.json();
          if (sessions.length > 0) {
            this.currentSession = sessions[0];
          }
        }
      }

      // Load from local storage (filtered by school)
      if (!this.currentSession) {
        const sessions = await db.getForSchool('attendanceSessions');
        const sessionForClass = sessions.find(s => s.classId === classId && s.date === date);
        
        this.currentSession = sessionForClass || {
          classId,
          date,
          subjectId,
          schoolId: this.authManager?.getSchoolId(),
          records: {}
        };
      }

      // Load students
      await this.loadStudentsForSession();
      
      // Render UI
      this.renderStudentsList();
      this.updateCounts();
      
      this.showMessage('Session loaded', 'success');
    } catch (error) {
      console.error('Error loading session:', error);
      this.showMessage('Error loading session', 'error');
    }
  }

  async loadStudentsForSession() {
    const classId = document.getElementById('classSelect').value;
    
    // Get students from class
    this.students = await db.getAllFromStore('students').then(all => 
      all.filter(s => s.current_class === parseInt(classId))
    );

    // Load attendance records from local storage
    this.attendanceRecords = this.currentSession.records || {};
  }

  renderStudentsList() {
    const container = document.getElementById('studentsList');
    const emptyState = document.getElementById('emptyState');
    
    container.innerHTML = '';

    if (this.students.length === 0) {
      emptyState.classList.remove('hidden');
      return;
    }

    emptyState.classList.add('hidden');

    this.students.forEach(student => {
      const studentId = student.id;
      const record = this.attendanceRecords[studentId] || { status: 'P' };
      
      const row = document.createElement('tr');
      row.className = 'hover:bg-gray-50';
      row.innerHTML = `
        <td class="p-3 font-mono text-sm">${student.admission_number}</td>
        <td class="p-3">${student.name}</td>
        <td class="p-3 text-center">
          <div class="flex gap-1 justify-center">
            <button class="status-btn px-2 py-1 rounded text-xs font-medium ${
              record.status === 'P' ? 'bg-green-500 text-white' : 'bg-gray-200'
            }" data-student="${studentId}" data-status="P">P</button>
            <button class="status-btn px-2 py-1 rounded text-xs font-medium ${
              record.status === 'A' ? 'bg-red-500 text-white' : 'bg-gray-200'
            }" data-student="${studentId}" data-status="A">A</button>
            <button class="status-btn px-2 py-1 rounded text-xs font-medium ${
              record.status === 'L' ? 'bg-yellow-500 text-white' : 'bg-gray-200'
            }" data-student="${studentId}" data-status="L">L</button>
            <button class="status-btn px-2 py-1 rounded text-xs font-medium ${
              record.status === 'E' ? 'bg-blue-500 text-white' : 'bg-gray-200'
            }" data-student="${studentId}" data-status="E">E</button>
          </div>
        </td>
        <td class="p-3">
          <input type="text" class="remarks-input w-full p-1 border border-gray-300 rounded text-xs" 
                 data-student="${studentId}" value="${record.remarks || ''}" placeholder="Remarks">
        </td>
      `;
      
      // Add event listeners
      row.querySelectorAll('.status-btn').forEach(btn => {
        btn.addEventListener('click', (e) => this.markAttendance(
          parseInt(btn.dataset.student),
          btn.dataset.status,
          row
        ));
      });

      row.querySelector('.remarks-input').addEventListener('change', (e) => {
        this.attendanceRecords[studentId].remarks = e.target.value;
      });
      
      container.appendChild(row);
    });
  }

  markAttendance(studentId, status, row = null) {
    this.attendanceRecords[studentId] = {
      status,
      remarks: this.attendanceRecords[studentId]?.remarks || ''
    };

    // Update UI
    if (!row) {
      const buttons = document.querySelectorAll(`[data-student="${studentId}"]`);
      buttons.forEach(btn => {
        btn.classList.remove('bg-green-500', 'bg-red-500', 'bg-yellow-500', 'bg-blue-500', 'text-white');
        btn.classList.add('bg-gray-200');
        if (btn.dataset.status === status) {
          btn.classList.add('bg-green-500', 'text-white');
        }
      });
    }

    this.updateCounts();
  }

  markAllPresent() {
    this.students.forEach(student => {
      this.markAttendance(student.id, 'P');
    });
    this.renderStudentsList();
    this.showMessage('All marked as present', 'success');
  }

  resetForm() {
    this.attendanceRecords = {};
    this.currentSession = null;
    this.renderStudentsList();
    this.updateCounts();
  }

  updateCounts() {
    const counts = { P: 0, A: 0, L: 0, E: 0 };
    
    Object.values(this.attendanceRecords).forEach(record => {
      counts[record.status]++;
    });

    document.getElementById('presentCount').textContent = counts.P;
    document.getElementById('absentCount').textContent = counts.A;
    document.getElementById('lateCount').textContent = counts.L;
    document.getElementById('totalCount').textContent = this.students.length;
  }

  async saveAttendance() {
    const classId = document.getElementById('classSelect').value;
    const date = document.getElementById('attendanceDate').value;

    if (!classId || !date) {
      this.showMessage('Please select class and date', 'warning');
      return;
    }

    try {
      // Get current school context
      const schoolId = this.authManager?.getSchoolId();
      if (!schoolId) {
        this.showMessage('No school context. Please re-login.', 'error');
        return;
      }
      
      // Save individual records to IndexedDB for offline-first
      const sessionId = this.currentSession?.id || `session_${classId}_${date}_${Date.now()}`;
      
      for (const [studentId, record] of Object.entries(this.attendanceRecords)) {
        await db.saveAttendanceRecord({
          id: `${sessionId}_${studentId}`,
          sessionId,
          studentId: parseInt(studentId),
          status: record.status,
          remarks: record.remarks || '',
          synced: false,
          schoolId,
          markedAt: new Date().toISOString()
        });
      }

      // Save session with school_id
      await db.saveSession({
        id: sessionId,
        classId: parseInt(classId),
        date,
        status: 'open',
        synced: false,
        schoolId,
        recordCount: Object.keys(this.attendanceRecords).length
      });

      // Queue for sync
      this.syncManager.queueChange('attendance_batch', {
        sessionId,
        classId: parseInt(classId),
        date,
        schoolId,
        records: this.attendanceRecords
      });

      // Try to sync if online
      if (navigator.onLine) {
        await this.syncManager.syncPending();
      }

      this.showMessage('Attendance saved' + (navigator.onLine ? ' and synced' : ' (will sync when online)'), 'success');
    } catch (error) {
      console.error('Error saving attendance:', error);
      this.showMessage('Error saving attendance', 'error');
    }
  }

  async syncToServer() {
    try {
      const records = Object.entries(this.attendanceRecords).map(([studentId, data]) => ({
        student_id: parseInt(studentId),
        status: data.status,
        remarks: data.remarks,
        marked_at: new Date().toISOString()
      }));

      const response = await fetch(`${this.apiBase}/attendance/records/sync_batch/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.currentSession.id,
          records
        })
      });

      if (response.ok) {
        const result = await response.json();
        this.showMessage(
          `Synced: ${result.created} new, ${result.updated} updated`,
          'success'
        );
      }
    } catch (error) {
      console.error('Sync error:', error);
      this.showMessage('Error syncing (changes saved locally)', 'warning');
    }
  }

  async closeSession() {
    if (!this.currentSession) {
      this.showMessage('No session to close', 'warning');
      return;
    }

    try {
      if (navigator.onLine) {
        await fetch(`${this.apiBase}/attendance/sessions/${this.currentSession.id}/close/`, {
          method: 'POST'
        });
      }
      
      this.currentSession = null;
      this.attendanceRecords = {};
      this.renderStudentsList();
      this.showMessage('Session closed', 'success');
    } catch (error) {
      console.error('Error closing session:', error);
      this.showMessage('Error closing session', 'error');
    }
  }

  filterStudents(query) {
    const rows = document.querySelectorAll('#studentsList tr');
    const lowerQuery = query.toLowerCase();

    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(lowerQuery) ? '' : 'none';
    });
  }

  exportAsCSV() {
    const classId = document.getElementById('classSelect').value;
    const date = document.getElementById('attendanceDate').value;

    if (!classId || !date) {
      this.showMessage('Please select class and date', 'warning');
      return;
    }

    let csv = 'Admission No.,Name,Status,Remarks\n';

    this.students.forEach(student => {
      const record = this.attendanceRecords[student.id] || { status: 'P' };
      const statusMap = { P: 'Present', A: 'Absent', L: 'Late', E: 'Excused' };
      csv += `${student.admission_number},"${student.name}",${statusMap[record.status]},"${record.remarks || ''}"\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_${classId}_${date}.csv`;
    a.click();
  }

  async updateSyncStatus() {
    const syncStatus = document.getElementById('syncStatus');
    const offlineWarning = document.getElementById('offlineWarning');
    
    if (!syncStatus) return;

    if (this.syncManager.isSyncing) {
      syncStatus.textContent = '⏳ Syncing...';
      syncStatus.className = 'text-sm px-3 py-1 rounded bg-blue-100 text-blue-800';
    } else if (this.syncManager.syncQueue.length > 0) {
      syncStatus.textContent = `📝 ${this.syncManager.syncQueue.length} pending`;
      syncStatus.className = 'text-sm px-3 py-1 rounded bg-yellow-100 text-yellow-800';
    } else if (navigator.onLine) {
      syncStatus.textContent = '✓ Synced';
      syncStatus.className = 'text-sm px-3 py-1 rounded bg-green-100 text-green-800';
    } else {
      syncStatus.textContent = '🔴 Offline';
      syncStatus.className = 'text-sm px-3 py-1 rounded bg-red-100 text-red-800';
    }

    // Show/hide offline warning
    if (offlineWarning) {
      if (!navigator.onLine && this.syncManager.syncQueue.length > 0) {
        offlineWarning.classList.remove('hidden');
      } else {
        offlineWarning.classList.add('hidden');
      }
    }
  }

  filterStudents(query) {
    const rows = document.querySelectorAll('#studentsList tr');
    const lowerQuery = query.toLowerCase();
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(lowerQuery) ? '' : 'none';
    });
  }

  showMessage(message, type = 'info') {
    // Create a simple notification
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-3 rounded-lg shadow-lg text-white text-sm z-50 ${
      type === 'success' ? 'bg-green-500' :
      type === 'error' ? 'bg-red-500' :
      type === 'warning' ? 'bg-yellow-500' :
      'bg-blue-500'
    }`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.remove(), 3000);
  }
}

// Initialize when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.attendanceController = new AttendanceController();
  });
} else {
  window.attendanceController = new AttendanceController();
}
