const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync('index.html', 'utf8');
const appScript = fs.readFileSync('assets/app.js', 'utf8');
assert(appScript.includes('function calculateMeds'), 'Application JavaScript asset not found');

const elements = new Map();
function makeElement(value = '') {
  return {
    value,
    innerHTML: '',
    textContent: '',
    className: '',
    dataset: {},
    classList: { add() {}, remove() {} },
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
global.navigator = {};
global.fetch = async () => { throw new Error('not used in calculator tests'); };

global.URL = URL;
vm.runInThisContext(appScript, { filename: 'assets/app.js' });
const event = { preventDefault() {} };

// Unit conversion regression: 1 g prescribed, 500 mg in 5 mL => 10 mL.
set('med-presc', '1');
set('med-presc-unit', 'g');
set('med-disp', '500');
set('med-disp-unit', 'mg');
set('med-vol', '5');
const medResult = set('med-result');
calculateMeds(event);
assert(medResult.innerHTML.includes('10.00 mL'));

// Incompatible units must fail closed.
elements.get('med-presc-unit').value = 'UI';
elements.get('med-disp-unit').value = 'mg';
calculateMeds(event);
assert(medResult.innerHTML.includes('precisam ser compatíveis'));

// Pediatric BMI must not use adult cut-offs.
set('bmi-w', '30');
set('bmi-h', '1.3');
set('bmi-age', '10');
const bmiResult = set('bmi-result');
calculateBMI(event);
assert(bmiResult.innerHTML.includes('Classificação pediátrica não calculada'));

// McDonald rounding must never report seven days.
set('au-input', '23.6');
const mcResult = set('mcdonald-result');
calculateMcDonald(event);
assert(!mcResult.innerHTML.includes('7 dias'));

// GCS starts incomplete and supports NT without a numeric total.
set('glasgow-e', '');
set('glasgow-v', '');
set('glasgow-m', '');
const gcsTotal = set('glasgow-total');
set('glasgow-note');
scoreGlasgow();
assert.strictEqual(gcsTotal.textContent, '—');
elements.get('glasgow-e').value = '4';
elements.get('glasgow-v').value = 'NT';
elements.get('glasgow-m').value = '6';
scoreGlasgow();
assert.strictEqual(gcsTotal.textContent, 'NT');

// Apgar starts incomplete rather than silently displaying 10.
set('apgar-time', '');
for (const id of ['apgar-a', 'apgar-p', 'apgar-g', 'apgar-t', 'apgar-r']) set(id, '');
const apgarTotal = set('apgar-total');
set('apgar-note');
scoreApgar();
assert.strictEqual(apgarTotal.textContent, '—');

console.log('frontend_qc: calculator assertions passed');

// Frontend should consume the typed/versioned API, not legacy compatibility routes.
assert(appScript.includes("fetch('/api/v1/healthz'"));
assert(appScript.includes('fetch(`/api/v1/sae/search'));
assert(appScript.includes('fetch(`/api/v1/policies/'));
assert(appScript.includes('data.items.map'));
assert(appScript.includes('mapping_confidence'));
assert(appScript.includes('mapping_rationale'));
assert(appScript.includes('safeExternalUrl'));
assert(appScript.includes('/docs/Nanda-I%202024-2026.pdf#page='));

// Production/static hardening regressions.
assert(!html.includes('cdn.tailwindcss.com'));
assert(html.includes('href="/assets/app.css"'));
assert(html.includes('rel="icon" href="/favicon.ico" sizes="any"'));
assert(html.includes('rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png"'));
assert(html.includes('rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png"'));
assert(html.includes('rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png"'));
assert(html.includes('<script src="/assets/app.js" defer></script>'));
assert(html.includes('/docs/Nanda-I%202024-2026.pdf'));
assert(!html.includes('onclick='));
assert(!html.includes('onsubmit='));
assert(!html.includes('onchange='));
assert(!/<script>([\s\S]*?)<\/script>/.test(html));
assert(html.includes('role="tablist"'));
assert(html.includes('aria-selected="true"'));
assert(html.includes('data-tab="sae"'));
assert(html.includes('data-policy="PNAISM"'));

console.log('frontend_qc: static hardening assertions passed');
assert(appScript.includes('function renderContextualLinks'));
assert(appScript.includes('alternativas contextuais'));
assert(appScript.includes('nic_links'));
assert(appScript.includes('noc_links'));
console.log('frontend_qc: contextual NNN rendering assertions passed');


// Pass 6.1 PWA/offline regressions.
const manifest = JSON.parse(fs.readFileSync('manifest.json', 'utf8'));
assert(manifest.icons.length >= 2);
assert(manifest.icons.every((icon) => icon.src.startsWith('/assets/icons/')));
assert(manifest.icons.every((icon) => !icon.src.includes('://')));
const sw = fs.readFileSync('sw.js', 'utf8');
assert(sw.includes("clinical-reference-v19-v2-brazil-oxygenation"));
assert(sw.includes('/assets/offline/sae.json'));
assert(sw.includes('/assets/offline/policies.json'));
assert(sw.includes("cache: 'reload'"));
assert(sw.includes('offlineSaeSearch'));
assert(sw.includes('offlinePolicy'));
assert(html.includes('/manifest.json?v=611'));
assert(appScript.includes('responseFromOfflineCache'));
assert(appScript.includes("X-Clinical-Offline"));
assert(appScript.includes('async function searchSaeOffline'));
assert(appScript.includes('async function policyOffline'));
assert(appScript.includes('Modo Offline · dados locais'));
assert(appScript.includes('Racional técnico (EN)'));
assert(appScript.includes('Aplicabilidade (PT-BR)'));
assert(appScript.includes('Applicability (EN-GB)'));
assert(appScript.includes('link.applicability_pt || link.applicability'));
assert(appScript.includes('link.applicability_en || link.applicability'));
assert(
  appScript.indexOf('Aplicabilidade (PT-BR)') <
  appScript.indexOf('Applicability (EN-GB)')
);
console.log('frontend_qc: Pass 6.1 offline/localisation assertions passed');

assert(appScript.includes('item.intervention_pt'));
assert(appScript.includes('item.intervention_en'));
assert(appScript.includes('item.outcome_pt'));
assert(appScript.includes('item.outcome_en'));

assert(appScript.includes('lang="pt-BR"'));
assert(appScript.includes('lang="en-GB"'));

assert(appScript.includes('PT-BR:'));
assert(appScript.includes('EN-GB:'));

assert(
  sw.includes('clinical-reference-v19-v2-brazil-oxygenation')
);

console.log(
  'frontend_qc: F-04 bilingual applicability rendering assertions passed'
);

