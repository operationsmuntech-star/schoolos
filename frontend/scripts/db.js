/**
 * IndexedDB Wrapper - Offline data persistence
 * Phase 1: Complete attendance data management
 */

class IndexedDBManager {
  constructor(dbName = 'SchoolApp', version = 2) {
    this.dbName = dbName;
    this.version = version;
    this.db = null;
    this.stores = [
      'appSettings', 'syncQueue', 'attendanceSessions', 'attendanceRecords',
      'exceptions', 'classes', 'students', 'teachers', 'subjects', 'terms'
    ];
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        console.log('✓ IndexedDB initialized');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create stores if they don't exist
        for (const storeName of this.stores) {
          if (!db.objectStoreNames.contains(storeName)) {
            const store = db.createObjectStore(storeName, { keyPath: 'id' });

            // Add indexes based on store type
            if (storeName === 'syncQueue') {
              store.createIndex('status', 'status', { unique: false });
              store.createIndex('timestamp', 'timestamp', { unique: false });
            } else if (storeName === 'attendanceSessions') {
              store.createIndex('date', 'date', { unique: false });
              store.createIndex('synced', 'synced', { unique: false });
            } else if (storeName === 'attendanceRecords') {
              store.createIndex('sessionId', 'sessionId', { unique: false });
              store.createIndex('studentId', 'studentId', { unique: false });
              store.createIndex('status', 'status', { unique: false });
              store.createIndex('synced', 'synced', { unique: false });
            }
          }
        }
      };
    });
  }

  async addToStore(storeName, data) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      // Auto-add school_id for tenant isolation
      const dataWithSchool = {
        ...data,
        id: data.id || this.generateId(),
        schoolId: data.schoolId || this.getCurrentSchoolId(),
        createdAt: data.createdAt || new Date().toISOString()
      };
      
      const request = store.add(dataWithSchool);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async updateInStore(storeName, data) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      // Preserve school_id
      const dataWithSchool = {
        ...data,
        schoolId: data.schoolId || this.getCurrentSchoolId(),
        updatedAt: new Date().toISOString()
      };
      
      const request = store.put(dataWithSchool);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async getFromStore(storeName, id) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(id);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async getAllFromStore(storeName, indexName = null, value = null) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      let request;

      if (indexName && value !== null) {
        const index = store.index(indexName);
        request = index.getAll(value);
      } else {
        request = store.getAll();
      }

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        // Filter results by school_id for tenant isolation
        const allRecords = request.result || [];
        const currentSchoolId = this.getCurrentSchoolId();
        const filtered = allRecords.filter(record => 
          !record.schoolId || record.schoolId === currentSchoolId
        );
        resolve(filtered);
      };
    });
  }

  async deleteFromStore(storeName, id) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(id);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(true);
    });
  }

  async clearStore(storeName) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.clear();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(true);
    });
  }

  async queryByIndex(storeName, indexName, value) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const index = store.index(indexName);
      const request = index.getAll(value);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async queryRange(storeName, indexName, lower, upper) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const index = store.index(indexName);
      const range = IDBKeyRange.bound(lower, upper);
      const request = index.getAll(range);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async saveSession(sessionData) {
    const session = {
      id: sessionData.id || this.generateId(),
      classId: sessionData.classId,
      date: sessionData.date,
      subject: sessionData.subject,
      teacherId: sessionData.teacherId,
      status: sessionData.status || 'open',
      synced: sessionData.synced || false,
      recordCount: sessionData.recordCount || 0,
      schoolId: sessionData.schoolId || this.getCurrentSchoolId(),
      ...sessionData,
      savedAt: new Date().toISOString()
    };

    return this.updateInStore('attendanceSessions', session);
  }

  async getSession(sessionId) {
    return this.getFromStore('attendanceSessions', sessionId);
  }

  async getSessions(classId, date) {
    const allSessions = await this.getAllFromStore('attendanceSessions');
    return allSessions.filter(s => s.classId === classId && s.date === date);
  }

  async saveAttendanceRecord(recordData) {
    const record = {
      id: recordData.id || this.generateId(),
      sessionId: recordData.sessionId,
      studentId: recordData.studentId,
      status: recordData.status,
      remarks: recordData.remarks || '',
      synced: recordData.synced || false,
      schoolId: recordData.schoolId || this.getCurrentSchoolId(),
      ...recordData,
      savedAt: new Date().toISOString()
    };

    return this.updateInStore('attendanceRecords', record);
  }

  async getAttendanceRecord(recordId) {
    return this.getFromStore('attendanceRecords', recordId);
  }

  async getSessionAttendance(sessionId) {
    const records = await this.queryByIndex('attendanceRecords', 'sessionId', sessionId);
    const schoolId = this.getCurrentSchoolId();
    return records.filter(r => !r.schoolId || r.schoolId === schoolId);
  }

  async getStudentAttendance(studentId, limit = 100) {
    const records = await this.queryByIndex('attendanceRecords', 'studentId', studentId);
    const schoolId = this.getCurrentSchoolId();
    const filtered = records.filter(r => !r.schoolId || r.schoolId === schoolId);
    return filtered.slice(-limit);
  }

  async getUnsyncedRecords(limit = 1000) {
    const records = await this.queryByIndex('attendanceRecords', 'synced', false);
    const schoolId = this.getCurrentSchoolId();
    const filtered = records.filter(r => !r.schoolId || r.schoolId === schoolId);
    return filtered.slice(0, limit);
  }

  async markRecordsSynced(recordIds) {
    for (const recordId of recordIds) {
      const record = await this.getFromStore('attendanceRecords', recordId);
      if (record) {
        await this.updateInStore('attendanceRecords', {
          ...record,
          synced: true,
          syncedAt: new Date().toISOString()
        });
      }
    }
    return recordIds.length;
  }

  async getSyncQueueItems() {
    return this.queryByIndex('syncQueue', 'status', 'pending');
  }

  async saveClasses(classes) {
    for (const klass of classes) {
      await this.updateInStore('classes', {
        id: klass.id,
        name: klass.name,
        ...klass
      });
    }
  }

  async saveStudents(students) {
    for (const student of students) {
      await this.updateInStore('students', {
        id: student.id,
        name: student.name,
        admissionNo: student.admission_no,
        ...student
      });
    }
  }

  async getSize() {
    let total = 0;
    for (const storeName of this.stores) {
      try {
        const items = await this.getAllFromStore(storeName);
        items.forEach(item => {
          total += JSON.stringify(item).length;
        });
      } catch (e) {
        console.error(`Error getting size for ${storeName}:`, e);
      }
    }
    return (total / 1024 / 1024).toFixed(2);
  }

  async clearAll() {
    for (const storeName of this.stores) {
      await this.clearStore(storeName);
    }
    console.log('✓ All stores cleared');
  }

  generateId() {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Multi-tenant helpers
  getCurrentSchoolId() {
    try {
      return window.authManager?.getSchoolId() || null;
    } catch (e) {
      console.warn('Could not get school ID from authManager:', e);
      return null;
    }
  }

  getCurrentSchoolCode() {
    try {
      return window.authManager?.getSchoolCode() || null;
    } catch (e) {
      console.warn('Could not get school code from authManager:', e);
      return null;
    }
  }

  async getForSchool(storeName, schoolId = null) {
    const sid = schoolId || this.getCurrentSchoolId();
    if (!sid) {
      console.warn('No school ID available');
      return [];
    }
    const allRecords = await this.getAllFromStore(storeName);
    return allRecords.filter(record => record.schoolId === sid);
  }

  async clearForSchool(storeName, schoolId = null) {
    const sid = schoolId || this.getCurrentSchoolId();
    if (!sid) {
      throw new Error('No school ID available');
    }
    const records = await this.getForSchool(storeName, sid);
    for (const record of records) {
      await this.deleteFromStore(storeName, record.id);
    }
    return records.length;
  }
}

// Initialize IndexedDB manager globally
window.db = new IndexedDBManager();
window.db.init().catch(e => console.error('IndexedDB init error:', e));
