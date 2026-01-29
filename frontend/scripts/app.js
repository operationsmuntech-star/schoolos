if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js').then(() => console.log('SW registered'));
}

window.addEventListener('online', () => document.getElementById('status').textContent = 'Online');
window.addEventListener('offline', () => document.getElementById('status').textContent = 'Offline');
