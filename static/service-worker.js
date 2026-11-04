const CACHE_NAME = 'fem-cache-v1';
const STATIC_ASSETS = [
  '/',
  '/static/css/variables.css',
  '/static/css/base.css',
  '/static/css/navbar.css',
  '/static/css/sidebar.css',
  '/static/css/buttons.css',
  '/static/css/cards.css',
  '/static/css/forms.css',
  '/static/css/dashboard.css',
  '/static/css/community.css',
  '/static/css/stories.css',
  '/static/css/sync.css',
  '/static/css/responsive.css',
  '/static/js/indexeddb.js',
  '/static/js/sync.js',
  '/static/js/offline.js',
  '/static/js/main.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('Some assets could not be cached immediately:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;

  // Don't intercept POST requests or sync API batch
  if (request.method !== 'GET' || request.url.includes('/api/sync/')) {
    return;
  }

  // Network First, fallback to cache
  event.respondWith(
    fetch(request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // If HTML navigation request fails while offline, return cached landing or home
          if (request.headers.get('accept').includes('text/html')) {
            return caches.match('/');
          }
        });
      })
  );
});
