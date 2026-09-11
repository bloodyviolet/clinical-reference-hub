const CACHE_NAME = 'clinical-reference-v13-v2-metabolic';
const OFFLINE_SAE_URL = '/assets/offline/sae.json';
const OFFLINE_POLICIES_URL = '/assets/offline/policies.json';
const APP_SHELL = [
  '/',
  '/manifest.json?v=611',
  '/assets/app.css',
  '/assets/i18n.js',
  '/assets/clinical-tools.js',
  '/assets/app.js',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png',
  '/assets/icons/apple-touch-icon.png',
  '/assets/icons/favicon-32.png',
  '/assets/icons/favicon-16.png',
  '/favicon.ico',
  OFFLINE_SAE_URL,
  OFFLINE_POLICIES_URL,
];

function jsonResponse(payload, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Clinical-Offline': '1',
      ...extraHeaders,
    },
  });
}

function normalise(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR');
}

async function cachedJson(path) {
  const response = await caches.match(path, { ignoreSearch: true });
  if (!response || !response.ok) {
    throw new Error(`Offline bundle unavailable: ${path}`);
  }
  return response.json();
}

async function offlineSaeSearch(url) {
  const bundle = await cachedJson(OFFLINE_SAE_URL);
  const query = (url.searchParams.get('q') || '').trim();
  const limit = Math.min(Math.max(Number.parseInt(url.searchParams.get('limit') || '20', 10) || 20, 1), 100);
  const offset = Math.max(Number.parseInt(url.searchParams.get('offset') || '0', 10) || 0, 0);

  if (!query) {
    return jsonResponse({ detail: 'Search query cannot be blank.' }, 422);
  }

  const needle = normalise(query);
  const allMatches = bundle.items.filter((item) => {
    const links = [...(item.nic_links || []), ...(item.noc_links || [])];
    const fields = [
      item.code, item.description_pt, item.description_en,
      item.nic_code, item.nic_label_pt, item.nic_label_en,
      item.noc_code, item.noc_label_pt, item.noc_label_en,
      ...links.flatMap((link) => [link.code, link.label_pt, link.label_en]),
    ];
    return fields.some((value) => normalise(value).includes(needle));
  });

  const items = allMatches.slice(offset, offset + limit);
  if (!items.length) {
    return jsonResponse({ detail: `Nenhum diagnóstico encontrado para a busca: '${query}'` }, 404);
  }

  return jsonResponse({
    query,
    limit,
    offset,
    returned: items.length,
    items,
  });
}

async function offlinePolicy(url) {
  const bundle = await cachedJson(OFFLINE_POLICIES_URL);
  const prefix = '/api/v1/policies/';
  const raw = decodeURIComponent(url.pathname.slice(prefix.length));
  const key = raw.trim().toUpperCase();
  const data = bundle.policies?.[key];
  if (!data) {
    return jsonResponse({ detail: `No directives found for policy: ${key}` }, 404);
  }
  return jsonResponse(data);
}

async function offlineApiFallback(url) {
  if (url.pathname === '/api/v1/sae/search') {
    return offlineSaeSearch(url);
  }
  if (url.pathname.startsWith('/api/v1/policies/')) {
    return offlinePolicy(url);
  }
  return jsonResponse({ detail: 'API unavailable while offline.' }, 503);
}

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Force a network revalidation for every shell resource so an older browser
    // HTTP/manifest cache cannot seed the new service-worker cache with Pass 6 files.
    for (const url of APP_SHELL) {
      const request = new Request(url, { cache: 'reload' });
      const response = await fetch(request);
      if (!response.ok) {
        throw new Error(`Failed to precache ${url}: HTTP ${response.status}`);
      }
      await cache.put(url, response.clone());
    }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const sameOrigin = url.origin === self.location.origin;
  const isApiRequest = sameOrigin && (
    url.pathname.startsWith('/api/v1/') ||
    url.pathname.startsWith('/sae/') ||
    url.pathname.startsWith('/policy/') ||
    url.pathname.startsWith('/pnaism/') ||
    url.pathname === '/healthz'
  );

  if (isApiRequest) {
    event.respondWith((async () => {
      try {
        // Online API remains authoritative.
        return await fetch(event.request);
      } catch (_) {
        // For the two browser-facing clinical flows, synthesize an API-compatible
        // response directly from the precached complete bundles. This avoids a
        // fragile second fetch/fallback round trip in app.js.
        return offlineApiFallback(url);
      }
    })());
    return;
  }

  event.respondWith((async () => {
    try {
      const response = await fetch(event.request);
      if (response.ok && sameOrigin) {
        const cache = await caches.open(CACHE_NAME);
        await cache.put(event.request, response.clone());
      }
      return response;
    } catch (_) {
      const cached = await caches.match(event.request, { ignoreSearch: true });
      if (cached) return cached;
      if (event.request.mode === 'navigate') {
        const shell = await caches.match('/');
        if (shell) return shell;
      }
      return new Response('Recurso indisponível offline.', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }
  })());
});
