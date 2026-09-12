const VERSION = '__BUILD_VERSION__';
const CACHE_NAME = 'kokeniwa-' + VERSION;
const CORE = [
  '/',
  '/static/manifest.webmanifest',
  '/static/style.css',
  '/static/experience.css',
  '/static/garden.css',
  '/static/pwa.css',
  '/static/experience.js',
  '/static/pwa.js',
  '/static/pwa-icon-192.png',
  '/static/pwa-icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache =>
    Promise.all(CORE.map(url => fetch(url).then(response => {
      if (response.ok) return cache.put(url, response);
    }).catch(() => undefined)))
  ));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith('kokeniwa-') && key !== CACHE_NAME)
      .map(key => caches.delete(key))
  )).then(() => self.clients.claim()));
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response.ok) await cache.put(request, response.clone());
    return response;
  } catch (_) {
    return (await cache.match(request, {ignoreSearch: true})) ||
      (request.mode === 'navigate' && await cache.match('/')) ||
      Response.error();
  }
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || url.pathname === '/version.json') return;

  if (request.mode === 'navigate' || url.pathname.startsWith('/static/data/')) {
    event.respondWith(networkFirst(request));
    return;
  }
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(caches.match(request, {ignoreSearch: true}).then(cached =>
      cached || fetch(request).then(response => {
        if (!response.ok) return response;
        return caches.open(CACHE_NAME)
          .then(cache => cache.put(request, response.clone()))
          .then(() => response);
      })
    ));
    return;
  }
  event.respondWith(networkFirst(request));
});
