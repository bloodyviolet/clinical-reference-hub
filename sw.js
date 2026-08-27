self.addEventListener('install', (e) => {
  console.log('[Service Worker] Installed');
});
self.addEventListener('fetch', (e) => {
  e.respondWith(fetch(e.request).catch(() => new Response("Modo offline ativo.")));
});
