const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const appScript = fs.readFileSync('assets/app.js', 'utf8');
const saeBundle = JSON.parse(fs.readFileSync('assets/offline/sae.json', 'utf8'));
const policyBundle = JSON.parse(fs.readFileSync('assets/offline/policies.json', 'utf8'));

const elements = new Map();
function makeElement(value = '') {
  const classes = new Set();
  return {
    value,
    innerHTML: '',
    innerText: '',
    textContent: '',
    className: '',
    href: '',
    dataset: {},
    classList: {
      add(...names) { names.forEach((name) => classes.add(name)); },
      remove(...names) { names.forEach((name) => classes.delete(name)); },
      contains(name) { return classes.has(name); },
    },
    addEventListener() {},
    setAttribute() {},
    focus() {},
  };
}
function set(id, value = '') {
  const el = makeElement(value);
  elements.set(id, el);
  return el;
}

global.document = {
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, makeElement());
    return elements.get(id);
  },
  querySelectorAll() { return []; },
  addEventListener() {},
};
Object.defineProperty(global, 'navigator', { value: { onLine: false }, configurable: true });
global.window = { addEventListener() {} };
global.URL = URL;

global.fetch = async (url) => {
  const value = String(url);
  if (value === '/assets/offline/sae.json') {
    return { ok: true, status: 200, async json() { return saeBundle; } };
  }
  if (value === '/assets/offline/policies.json') {
    return { ok: true, status: 200, async json() { return policyBundle; } };
  }
  if (value.startsWith('/api/v1/')) {
    return {
      ok: false,
      status: 503,
      async json() { return { detail: 'API unavailable while offline.' }; },
    };
  }
  throw new Error(`unexpected fetch: ${value}`);
};

vm.runInThisContext(appScript, { filename: 'assets/app.js' });

(async () => {
  const byCode = await searchSaeOffline('00322');
  assert(byCode.items.some((item) => item.code === '00322'));

  const byNic = await searchSaeOffline('0620');
  assert(byNic.items.some((item) => item.code === '00322'));

  const byNoc = await searchSaeOffline('2015');
  assert(byNoc.items.some((item) => item.code === '00339'));

  const accentInsensitive = await searchSaeOffline('prontidao para um maior bem-estar espiritual');
  assert(accentInsensitive.items.some((item) => item.code === '00068'));

  const pnaism = await policyOffline('PNAISM');
  assert.strictEqual(pnaism.returned, 17);

  set('sae-input', '00322');
  const saeResult = set('sae-result');
  await searchSAE({ preventDefault() {} });
  assert(saeResult.innerHTML.includes('Modo offline'));
  assert(saeResult.innerHTML.includes('lang="pt-BR"'));
  assert(saeResult.innerHTML.includes('lang="en-GB"'));
  assert(saeResult.innerHTML.includes('PT-BR:'));
  assert(saeResult.innerHTML.includes('EN-GB:'));

  assert(saeResult.innerHTML.includes('00322'));
  assert(saeResult.innerHTML.includes('Urinary Retention Care'));
  assert(saeResult.innerHTML.includes('Cuidados na Retenção Urinária'));

  const policyResults = set('policy-results');
  set('policy-loading');
  set('pdf-link');
  await loadPolicy('PNAISM');
  assert(policyResults.innerHTML.includes('Modo offline'));
  assert(policyResults.innerHTML.includes('PNAISM'));

  set('api-status');
  set('api-status-dot');
  const statusText = set('api-status-text');
  await checkApiHealth();
  assert.strictEqual(statusText.textContent, 'Modo Offline · dados locais');

  console.log('offline_qc: SAE search, policy fallback, accent-insensitive search and status badge passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
