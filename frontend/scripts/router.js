/**
 * Router - Handle offline-safe routing
 * Phase 0: Skeleton routing for SPA navigation
 */
const routes = {
  '/': 'views/dashboard.html',
  '/dashboard': 'views/dashboard.html',
  '/attendance': 'views/attendance.html',
  '/academics': 'views/academics.html',
  '/settings': 'views/settings.html',
};

class Router {
  constructor() {
    this.currentRoute = '/dashboard';
    this.init();
  }

  init() {
    window.addEventListener('hashchange', () => this.navigate());
    this.navigate();
  }

  navigate(path = null) {
    const route = path || window.location.hash.slice(1) || '/dashboard';
    const filePath = routes[route] || routes['/'];
    this.loadView(filePath);
  }

  async loadView(filePath) {
    try {
      const response = await fetch(filePath);
      if (response.ok) {
        const html = await response.text();
        document.getElementById('app-container').innerHTML = html;
      } else {
        this.loadOfflineFallback();
      }
    } catch (error) {
      console.warn('Navigation error, checking cache:', error);
      this.loadOfflineFallback();
    }
  }

  loadOfflineFallback() {
    const main = document.querySelector('main');
    if (main) {
      main.innerHTML = '<p class="p-4 text-center text-gray-600">Content not available offline. Check your connection.</p>';
    }
  }
}

// Initialize router
window.router = new Router();
