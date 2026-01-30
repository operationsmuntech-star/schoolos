/**
 * Multi-Tenant Authentication Module
 * Handles school login, token management, tenant context
 */

class TenantAuthManager {
  constructor() {
    this.apiBase = '/api/v1';
    this.currentSchool = null;
    this.currentUser = null;
    this.accessToken = null;
    this.refreshToken = null;
    this.init();
  }

  init() {
    console.log('🔐 TenantAuthManager initialized');
    this.loadStoredAuth();
    this.setupInterceptors();
  }

  loadStoredAuth() {
    /**Load authentication from localStorage*/
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    
    const schoolId = localStorage.getItem('school_id');
    const schoolCode = localStorage.getItem('school_code');
    const schoolName = localStorage.getItem('school_name');
    const username = localStorage.getItem('username');

    if (schoolId && schoolCode) {
      this.currentSchool = {
        id: parseInt(schoolId),
        code: schoolCode,
        name: schoolName,
      };
    }

    if (username) {
      this.currentUser = { username };
    }

    console.log('📍 Tenant loaded:', this.currentSchool?.code);
  }

  async login(schoolCode, username, password) {
    /**Login to specific school"""
    try {
      const response = await fetch(`${this.apiBase}/auth/school-login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({
          school_code: schoolCode,
          username: username,
          password: password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Login failed');
      }

      const data = await response.json();

      // Store tokens and tenant info
      this.storeAuth(data);

      console.log('✅ Login successful for school:', schoolCode);
      return data;
    } catch (error) {
      console.error('❌ Login error:', error);
      throw error;
    }
  }

  storeAuth(data) {
    /**Store authentication data"""
    this.accessToken = data.access;
    this.refreshToken = data.refresh;
    this.currentSchool = data.school;
    this.currentUser = data.user;

    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('school_id', data.school.id);
    localStorage.setItem('school_code', data.school.code);
    localStorage.setItem('school_name', data.school.name);
    localStorage.setItem('username', data.user.username);
    localStorage.setItem('last_login', new Date().toISOString());
    
    // Persist tenant info into IndexedDB for offline use (non-blocking)
    try {
      if (window.db && typeof window.db.updateInStore === 'function') {
        window.db.updateInStore('appSettings', {
          id: 'tenant',
          schoolId: data.school.id,
          schoolCode: data.school.code,
          schoolName: data.school.name,
          savedAt: new Date().toISOString()
        }).catch(e => console.warn('Could not save tenant to IndexedDB:', e));
      }
    } catch (e) {
      console.warn('IndexedDB tenant save failed:', e);
    }
  }

  async logout() {
    /**Logout and clear stored data"""
    try {
      await fetch(`${this.apiBase}/auth/logout/`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
    } catch (e) {
      console.warn('Logout request failed:', e);
    }

    this.clearAuth();
    window.location.href = '/login';
  }

  clearAuth() {
    /**Clear all authentication data"""
    this.accessToken = null;
    this.refreshToken = null;
    this.currentSchool = null;
    this.currentUser = null;

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('school_id');
    localStorage.removeItem('school_code');
    localStorage.removeItem('school_name');
    localStorage.removeItem('username');
  }

  isAuthenticated() {
    /**Check if user is authenticated"""
    return !!this.accessToken && !!this.currentSchool;
  }

  getSchoolId() {
    /**Get current school ID"""
    return this.currentSchool?.id;
  }

  getSchoolCode() {
    /**Get current school code"""
    return this.currentSchool?.code;
  }

  getUsername() {
    /**Get current username"""
    return this.currentUser?.username;
  }

  getHeaders() {
    /**Get headers with authentication token"""
    const headers = {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    return headers;
  }

  setupInterceptors() {
    /**Setup fetch interceptors for automatic token injection"""
    const originalFetch = window.fetch;

    window.fetch = async (...args) => {
      let [resource, config] = args;

      // Only add auth headers to same-origin requests
      if (typeof resource === 'string' && (
        resource.startsWith('/api') || 
        resource.startsWith('http://' + window.location.host) ||
        resource.startsWith('https://' + window.location.host)
      )) {
        config = config || {};
        config.headers = config.headers || {};

        // Add tenant headers
        if (this.currentSchool) {
          config.headers['X-School-Id'] = this.currentSchool.id;
        }

        // Add auth token
        if (this.accessToken) {
          config.headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
      }

      let response = await originalFetch(resource, config);

      // Handle token expiration
      if (response.status === 401) {
        console.log('⏰ Token expired, attempting refresh...');
        
        if (this.refreshToken) {
          const refreshed = await this.refreshAccessToken();
          if (refreshed) {
            // Retry original request
            config.headers['Authorization'] = `Bearer ${this.accessToken}`;
            response = await originalFetch(resource, config);
          }
        }

        if (response.status === 401) {
          // Refresh failed, logout
          this.clearAuth();
          window.location.href = '/login';
        }
      }

      return response;
    };

    console.log('🔗 Fetch interceptors configured');
  }

  async refreshAccessToken() {
    /**Refresh access token using refresh token"""
    try {
      const response = await fetch('/api/token/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh: this.refreshToken,
        }),
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      this.accessToken = data.access;
      localStorage.setItem('access_token', data.access);

      console.log('✅ Token refreshed');
      return true;
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      return false;
    }
  }

  async switchSchool(schoolId) {
    /**Switch active school (admin only)"""
    try {
      const response = await fetch(`${this.apiBase}/auth/switch-school/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ school_id: schoolId }),
      });

      if (!response.ok) {
        throw new Error('Failed to switch school');
      }

      const data = await response.json();
      this.currentSchool = data.school;
      localStorage.setItem('school_id', data.school.id);
      localStorage.setItem('school_code', data.school.code);

      console.log('🔄 Switched to school:', data.school.code);
      window.location.reload();
      return data;
    } catch (error) {
      console.error('❌ School switch failed:', error);
      throw error;
    }
  }

  async getAvailableSchools() {
    /**Get schools user has access to"""
    try {
      const response = await fetch(`${this.apiBase}/auth/schools/`, {
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch schools');
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Failed to get schools:', error);
      return [];
    }
  }

  getTenantContext() {
    /**Get full tenant context for UI"""
    return {
      schoolId: this.getSchoolId(),
      schoolCode: this.getSchoolCode(),
      schoolName: this.currentSchool?.name,
      username: this.getUsername(),
      isAuthenticated: this.isAuthenticated(),
    };
  }

  redirectIfNotAuthenticated() {
    /**Redirect to login if not authenticated"""
    if (!this.isAuthenticated()) {
      window.location.href = '/login';
    }
  }
}

// Initialize globally
window.authManager = new TenantAuthManager();

// Redirect if not authenticated when page loads
document.addEventListener('DOMContentLoaded', () => {
  // Only check on non-login pages
  if (!window.location.pathname.includes('/login')) {
    window.authManager.redirectIfNotAuthenticated();
  }
});
