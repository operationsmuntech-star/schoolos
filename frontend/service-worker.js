const CACHE_NAME = 'muntech-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/styles/tailwind.css',
  '/styles/base.css',
  '/styles/theme.css',
  '/scripts/app.js',
  '/scripts/db.js',
  '/scripts/install.js',
  '/views/dashboard.html',
  '/views/attendance.html',
  '/views/academics.html',
  '/views/settings.html'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(key => key !== CACHE_NAME && caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  event.respondWith(caches.match(event.request).then(response => response || fetch(event.request)));
});
