const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const swSource = fs.readFileSync('sw.js', 'utf8');
const saeText = fs.readFileSync('assets/offline/sae.json', 'utf8');
const policyText = fs.readFileSync('assets/offline/policies.json', 'utf8');

const listeners = {};
const cacheEntries = new Map([
  ['/assets/offline/sae.json', new Response(saeText, { status: 200, headers: { 'Content-Type': 'application/json' } })],
  ['/assets/offline/policies.json', new Response(policyText, { status: 200, headers: { 'Content-Type': 'application/json' } })],
  ['/', new Response('<!doctype html><title>offline</title>', { status: 200, headers: { 'Content-Type': 'text/html' } })],
]);

global.self = {
  location: { origin: 'https://clinical-hub.duckdns.org' },
  addEventListener(type, handler) { listeners[type] = handler; },
  skipWaiting: async () => {},
  clients: { claim: async () => {} },
};

global.caches = {
  async match(request, options = {}) {
    let key = typeof request === 'string' ? request : new URL(request.url).pathname;
    if (!cacheEntries.has(key) && options.ignoreSearch && typeof request !== 'string') {
      key = new URL(request.url).pathname;
    }
    const value = cacheEntries.get(key);
    return value ? value.clone() : undefined;
  },
  async open() {
    return {
      async put(request, response) {
        const key = typeof request === 'string' ? request : new URL(request.url).pathname;
        cacheEntries.set(key, response.clone());
      },
    };
  },
  // Deliberately expose an obsolete F-01 cache so the current worker can exercise stale-cache cleanup.
  async keys() { return ['clinical-reference-v7-f01-bilingual']; },
  async delete() { return true; },
};

// Simulate a genuinely offline browser: every network request rejects.
global.fetch = async () => { throw new TypeError('Failed to fetch'); };

vm.runInThisContext(swSource, { filename: 'sw.js' });
assert(listeners.fetch, 'service worker fetch handler not registered');

async function dispatch(url, mode = 'cors') {
  let responsePromise;
  const request = mode === 'navigate'
    ? { url, method: 'GET', mode: 'navigate' }
    : new Request(url, { method: 'GET', mode });
  listeners.fetch({
    request,
    respondWith(value) { responsePromise = Promise.resolve(value); },
  });
  assert(responsePromise, `respondWith not called for ${url}`);
  return responsePromise;
}

(async () => {
  let response = await dispatch('https://clinical-hub.duckdns.org/api/v1/sae/search?q=0620&limit=50');
  assert.strictEqual(response.status, 200);
  assert.strictEqual(response.headers.get('X-Clinical-Offline'), '1');
  let payload = await response.json();
  assert(payload.items.some((item) => item.code === '00322'));

  response = await dispatch('https://clinical-hub.duckdns.org/api/v1/sae/search?q=2015&limit=50');
  assert.strictEqual(response.status, 200);
  payload = await response.json();
  assert(payload.items.some((item) => item.code === '00339'));

  response = await dispatch('https://clinical-hub.duckdns.org/api/v1/policies/PNAB');
  assert.strictEqual(response.status, 200);
  assert.strictEqual(response.headers.get('X-Clinical-Offline'), '1');
  payload = await response.json();
  assert.strictEqual(payload.policy_name, 'PNAB');
  assert(payload.returned > 0);

  response = await dispatch('https://clinical-hub.duckdns.org/api/v1/healthz');
  assert.strictEqual(response.status, 503);
  assert.strictEqual(response.headers.get('X-Clinical-Offline'), '1');

  // Cold offline navigation falls back to the precached root shell.
  response = await dispatch('https://clinical-hub.duckdns.org/some/deep/path', 'navigate');
  assert.strictEqual(response.status, 200);
  const html = await response.text();
  assert(html.includes('offline'));

  assert(swSource.includes("cache: 'reload'"), 'precache must force HTTP-cache revalidation');
  assert(swSource.includes("clinical-reference-v20-v2-brazil-methanol"));
  assert(swSource.includes("offlineSaeSearch"));
  assert(swSource.includes("offlinePolicy"));

  console.log('service_worker_offline_qc: synthetic SAE/policy API fallback and cold navigation passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
