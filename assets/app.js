function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function showError(elementId, message) {
  const res = document.getElementById(elementId);
  res.classList.remove('hidden');
  res.innerHTML = `<p class="text-sm font-medium text-rose-300">${escapeHtml(message)}</p>`;
}


function uiLanguage() {
  return (
    globalThis.ClinicalI18n
      ?.getLanguage?.()
    || 'pt-BR'
  );
}


function clinicalText(pt, en) {
  return uiLanguage() === 'en-GB'
    ? en
    : pt;
}

function safeExternalUrl(value) {
  try {
    const url = new URL(String(value));
    return url.protocol === 'https:' ? url.href : null;
  } catch (_) {
    return null;
  }
}

const OFFLINE_SAE_URL = '/assets/offline/sae.json';
const OFFLINE_POLICIES_URL = '/assets/offline/policies.json';
let offlineSaePromise = null;
let offlinePoliciesPromise = null;

function normaliseSearch(value) {
  return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
}

function confidencePt(value) {
  return ({ high: 'alta', moderate: 'moderada', review_required: 'revisão necessária' })[value] || value || '—';
}

function verificationPt(value) {
  return ({
    curated_current_edition: 'curado · edição atual',
    current_edition_verified: 'verificado · edição atual',
    contextual_current_edition: 'contextual · edição atual',
  })[value] || value || '—';
}

function mappingStatusPt(value) {
  return ({
    curated_current_editions_contextual: 'curadoria contextual · edições atuais',
  })[value] || value || '—';
}

async function responseFromOfflineCache(url) {
  if (typeof caches === 'undefined') return null;
  try {
    const cached = await caches.match(url, { ignoreSearch: true });
    return cached && cached.ok ? cached : null;
  } catch (_) {
    return null;
  }
}

async function loadOfflineSaeBundle() {
  if (!offlineSaePromise) {
    offlineSaePromise = (async () => {
      let response = await responseFromOfflineCache(OFFLINE_SAE_URL);
      if (!response) response = await fetch(OFFLINE_SAE_URL, { cache: 'force-cache' });
      if (!response.ok) throw new Error('Base SAE offline indisponível.');
      const data = await response.json();
      if (!Array.isArray(data.items) || data.count !== data.items.length) {
        throw new Error('Base SAE offline inválida.');
      }
      return data;
    })().catch((error) => {
      offlineSaePromise = null;
      throw error;
    });
  }
  return offlineSaePromise;
}

async function loadOfflinePoliciesBundle() {
  if (!offlinePoliciesPromise) {
    offlinePoliciesPromise = (async () => {
      let response = await responseFromOfflineCache(OFFLINE_POLICIES_URL);
      if (!response) response = await fetch(OFFLINE_POLICIES_URL, { cache: 'force-cache' });
      if (!response.ok) throw new Error('Base de políticas offline indisponível.');
      const data = await response.json();
      if (!data.policies || typeof data.policies !== 'object') {
        throw new Error('Base de políticas offline inválida.');
      }
      return data;
    })().catch((error) => {
      offlinePoliciesPromise = null;
      throw error;
    });
  }
  return offlinePoliciesPromise;
}

async function searchSaeOffline(query, limit = 50) {
  const bundle = await loadOfflineSaeBundle();
  const needle = normaliseSearch(query);
  const matches = bundle.items.filter((item) => {
    const links = [...(item.nic_links || []), ...(item.noc_links || [])];
    const fields = [
      item.code, item.description_pt, item.description_en,
      item.nic_code, item.nic_label_pt, item.nic_label_en,
      item.noc_code, item.noc_label_pt, item.noc_label_en,
      ...links.flatMap((link) => [link.code, link.label_pt, link.label_en]),
    ];
    return fields.some((value) => normaliseSearch(value).includes(needle));
  }).slice(0, limit);
  if (!matches.length) throw new Error(`Nenhum diagnóstico encontrado offline para a busca: '${query}'`);
  return { query, limit, offset: 0, returned: matches.length, items: matches };
}

async function policyOffline(policyName) {
  const bundle = await loadOfflinePoliciesBundle();
  const key = String(policyName || '').trim().toUpperCase();
  const data = bundle.policies[key];
  if (!data) throw new Error(`Diretriz ${key} não está disponível na base offline.`);
  return data;
}


function renderContextualLinks(links, classification) {
  const alternatives = Array.isArray(links) ? links.filter(link => link.role === 'alternative') : [];
  if (!alternatives.length) return '';
  const accent = classification === 'NIC' ? 'cyan' : 'emerald';
  return `
    <div class="bg-slate-950/50 border border-${accent}-900/40 rounded-xl p-4 space-y-3">
      <div class="flex items-center justify-between gap-3">
        <span class="text-xs font-bold text-${accent}-300 uppercase tracking-wider">${classification} · alternativas contextuais</span>
        <span class="text-[10px] text-slate-500">selecionar após avaliação</span>
      </div>
      <div class="space-y-2">
        ${alternatives.map(link => `
          <div class="border border-slate-800 rounded-lg p-3 bg-slate-900/50">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-mono text-xs font-bold text-${accent}-300">${escapeHtml(link.code)}</span>
              <span lang="pt-BR" class="text-xs font-semibold text-slate-100">${escapeHtml(link.label_pt)}</span>
              <span lang="en-GB" class="text-[10px] text-slate-500">${escapeHtml(link.label_en)}</span>
            </div>
            <p lang="pt-BR" class="text-[11px] text-slate-300 mt-2"><span class="font-semibold text-slate-400">Aplicabilidade (PT-BR):</span> ${escapeHtml(link.applicability_pt || link.applicability || '—')}</p>
            <p lang="en-GB" class="text-[11px] text-slate-300 mt-1"><span class="font-semibold text-slate-400">Applicability (EN-GB):</span> ${escapeHtml(link.applicability_en || link.applicability || '—')}</p>
            <p class="text-[10px] text-slate-500 mt-1">Confiança: ${escapeHtml(confidencePt(link.confidence))} · ${escapeHtml(verificationPt(link.verification_status))}</p>
          </div>
        `).join('')}
      </div>
    </div>`;
}

function isPositiveFinite(...values) {
  return values.every((value) => Number.isFinite(value) && value > 0);
}

function formatPositiveMeasurement(value, {
  decimalsAtOrAboveOne = 2,
  threshold = 0.001,
} = {}) {
  if (!Number.isFinite(value) || value <= 0) return '—';

  if (value < threshold) {
    return `<${threshold.toFixed(3)}`;
  }

  if (value >= 1) {
    return value.toFixed(decimalsAtOrAboveOne);
  }

  if (value >= 0.1) return value.toFixed(2);
  if (value >= 0.01) return value.toFixed(3);
  if (value >= 0.001) return value.toFixed(4);

  return value.toPrecision(3);
}

const DRIP_FACTORS = Object.freeze({
  macro: 20,
  micro: 60,
});

function switchTab(tab) {
  const views = ['sae', 'policy', 'calc', 'scales'];
  views.forEach(v => {
    const view = document.getElementById(`view-${v}`);
    const button = document.getElementById(`tab-btn-${v}`);
    view.classList.add('hidden');
    button.setAttribute('aria-selected', 'false');
    button.className = "whitespace-nowrap pb-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition";
  });
  document.getElementById(`view-${tab}`).classList.remove('hidden');
  document.getElementById(`tab-btn-${tab}`).setAttribute('aria-selected', 'true');
  document.getElementById(`tab-btn-${tab}`).className = "whitespace-nowrap pb-3 text-sm font-semibold border-b-2 border-teal-400 text-teal-300 transition";
}

async function checkApiHealth() {
  const badge = document.getElementById('api-status');
  const dot = document.getElementById('api-status-dot');
  const text = document.getElementById('api-status-text');
  try {
    const response = await fetch('/api/v1/healthz', { cache: 'no-store' });
    if (!response.ok) throw new Error('healthcheck failed');
    const health = await response.json();
    badge.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    dot.className = 'w-1.5 h-1.5 mr-1.5 rounded-full bg-emerald-400';
    text.textContent = health.sae_enabled ? 'API Online' : 'API Online · SAE desativado';
  } catch (_) {
    const offline = typeof navigator !== 'undefined' && navigator.onLine === false;
    badge.className = offline
      ? 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20'
      : 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20';
    dot.className = offline
      ? 'w-1.5 h-1.5 mr-1.5 rounded-full bg-amber-400'
      : 'w-1.5 h-1.5 mr-1.5 rounded-full bg-rose-400';
    text.textContent = offline ? 'Modo Offline · dados locais' : 'API Indisponível';
  }
}

async function searchSAE(event) {
  event.preventDefault();
  const query = document.getElementById('sae-input').value.trim();
  const container = document.getElementById('sae-result');
  container.classList.remove('hidden');

  if (!query || query.length > 100) {
    container.innerHTML = '<div class="bg-rose-950/30 border border-rose-800/50 p-4 rounded-xl text-rose-300 text-sm">Informe uma busca de 1 a 100 caracteres.</div>';
    return;
  }

  container.innerHTML = '<div class="text-sm text-slate-400">Consultando base clínica...</div>';
  try {
    let data;
    let source = 'api';
    try {
      const response = await fetch(`/api/v1/sae/search?q=${encodeURIComponent(query)}&limit=50`);
      if (!response.ok) {
        let message = 'Nenhum resultado encontrado.';
        try { message = (await response.json()).detail || message; } catch (_) {}
        const error = new Error(message);
        error.httpStatus = response.status;
        throw error;
      }
      data = await response.json();
      if (response.headers?.get?.('X-Clinical-Offline') === '1') source = 'offline';
    } catch (error) {
      if (error.httpStatus && error.httpStatus !== 503) throw error;
      data = await searchSaeOffline(query, 50);
      source = 'offline';
    }

    const sourceNotice = source === 'offline'
      ? '<div class="bg-amber-950/30 border border-amber-700/50 p-3 rounded-xl text-amber-200 text-xs mb-4">Modo offline: resultados fornecidos pela base clínica local empacotada nesta versão.</div>'
      : '';
    container.innerHTML = sourceNotice + data.items.map(item => `
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <span class="text-xs uppercase tracking-wider font-semibold text-teal-400">Código NANDA</span>
            <h3 class="text-2xl font-black text-white tracking-tight">${escapeHtml(item.code)}</h3>
          </div>
          <span class="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-xs font-mono">ID #${escapeHtml(item.id)}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-1">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Diagnóstico (PT-BR)</span>
            <p lang="pt-BR" class="text-sm font-medium text-slate-100">${escapeHtml(item.description_pt)}</p>
          </div>
          <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-1">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Diagnostic (EN-GB)</span>
            <p lang="en-GB" class="text-sm font-medium text-slate-100">${escapeHtml(item.description_en)}</p>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-slate-950/60 p-4 rounded-xl border border-cyan-900/50 space-y-2">
            <div class="flex items-center justify-between gap-3">
              <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider">NIC primária ${escapeHtml(item.nic_code || '—')}</span>
              <span class="text-[10px] text-slate-500">8ª edição</span>
            </div>
            <p lang="pt-BR" class="text-sm font-semibold text-slate-100">${escapeHtml(item.nic_label_pt || item.nic_label_en || '—')}</p>
            <p lang="en-GB" class="text-xs text-slate-400">${escapeHtml(item.nic_label_en || '')}</p>
            <div class="pt-2 border-t border-slate-800 space-y-2">
              <p lang="pt-BR" class="text-xs text-slate-300"><span class="font-semibold text-cyan-300">PT-BR:</span> ${escapeHtml(item.intervention_pt || '—')}</p>
              <p lang="en-GB" class="text-xs text-slate-300"><span class="font-semibold text-cyan-300">EN-GB:</span> ${escapeHtml(item.intervention_en || '—')}</p>
            </div>
          </div>
          <div class="bg-slate-950/60 p-4 rounded-xl border border-emerald-900/50 space-y-2">
            <div class="flex items-center justify-between gap-3">
              <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">NOC primário ${escapeHtml(item.noc_code || '—')}</span>
              <span class="text-[10px] text-slate-500">7ª edição</span>
            </div>
            <p lang="pt-BR" class="text-sm font-semibold text-slate-100">${escapeHtml(item.noc_label_pt || item.noc_label_en || '—')}</p>
            <p lang="en-GB" class="text-xs text-slate-400">${escapeHtml(item.noc_label_en || '')}</p>
            <div class="pt-2 border-t border-slate-800 space-y-2">
              <p lang="pt-BR" class="text-xs text-slate-300"><span class="font-semibold text-emerald-300">PT-BR:</span> ${escapeHtml(item.outcome_pt || '—')}</p>
              <p lang="en-GB" class="text-xs text-slate-300"><span class="font-semibold text-emerald-300">EN-GB:</span> ${escapeHtml(item.outcome_en || '—')}</p>
            </div>
          </div>
        </div>
        ${(Array.isArray(item.nic_links) && item.nic_links.some(link => link.role === 'alternative')) || (Array.isArray(item.noc_links) && item.noc_links.some(link => link.role === 'alternative')) ? `
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${renderContextualLinks(item.nic_links, 'NIC')}
            ${renderContextualLinks(item.noc_links, 'NOC')}
          </div>` : ''}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
          <div class="bg-slate-950/50 border border-slate-800 rounded-lg p-3"><span class="text-slate-500 uppercase font-semibold">NANDA-I</span><p class="text-slate-300 mt-1">Domínio ${escapeHtml(item.nanda_domain || '—')} · Classe ${escapeHtml(item.nanda_class || '—')} · p. ${escapeHtml(item.nanda_source_page || '—')}</p></div>
          <div class="bg-slate-950/50 border border-slate-800 rounded-lg p-3"><span class="text-slate-500 uppercase font-semibold">Confiança</span><p class="text-amber-200 mt-1">${escapeHtml(confidencePt(item.mapping_confidence))}</p></div>
          <div class="bg-slate-950/50 border border-slate-800 rounded-lg p-3"><span class="text-slate-500 uppercase font-semibold">Revisão</span><p class="text-slate-300 mt-1">${escapeHtml(item.mapping_review_date || '—')}</p></div>
        </div>
        <div class="text-[11px] text-slate-300 border-t border-slate-800 pt-3 space-y-2">
          <p><span class="font-semibold text-amber-200">Racional técnico (EN):</span> ${escapeHtml(item.mapping_rationale || '—')}</p>
          <p><span class="font-semibold text-amber-200">Status:</span> ${escapeHtml(mappingStatusPt(item.mapping_status))}</p>
          <p><span class="font-semibold text-amber-200">Metodologia (EN):</span> ${escapeHtml(item.mapping_methodology || '—')}</p>
          ${safeExternalUrl(item.mapping_reference) ? `<a class="inline-flex text-teal-300 hover:text-teal-200 underline underline-offset-2" href="${escapeHtml(safeExternalUrl(item.mapping_reference))}" target="_blank" rel="noopener noreferrer">Referência do mapeamento ↗</a>` : ''}
          ${item.nanda_pdf_page ? `<a class="ml-3 inline-flex text-teal-300 hover:text-teal-200 underline underline-offset-2" href="/docs/Nanda-I%202024-2026.pdf#page=${encodeURIComponent(item.nanda_pdf_page)}" target="_blank" rel="noopener noreferrer">Abrir NANDA-I na página citada ↗</a>` : ''}
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="bg-rose-950/30 border border-rose-800/50 p-4 rounded-xl text-rose-300 text-sm">${escapeHtml(err.message)}</div>`;
  }
}

async function loadPolicy(policyName) {
  const container = document.getElementById('policy-results');
  const loader = document.getElementById('policy-loading');
  const pdfBtn = document.getElementById('pdf-link');
  pdfBtn.classList.remove('hidden');
  pdfBtn.classList.add('inline-flex');
  pdfBtn.href = `/docs/${encodeURIComponent(policyName)}.pdf`;

  document.querySelectorAll('.policy-btn').forEach(btn => {
    if (btn.innerText.includes(policyName)) {
      btn.className = "policy-btn px-3.5 py-1.5 mt-2 rounded-lg text-xs font-semibold bg-teal-600 text-white border border-teal-500 transition shadow-lg shadow-teal-600/20";
    } else {
      btn.className = "policy-btn px-3.5 py-1.5 mt-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition";
    }
  });

  container.innerHTML = '';
  loader.classList.remove('hidden');
  try {
    let data;
    let source = 'api';
    try {
      const response = await fetch(`/api/v1/policies/${encodeURIComponent(policyName)}`);
      if (!response.ok) {
        let message = 'Não foi possível carregar as diretrizes.';
        try { message = (await response.json()).detail || message; } catch (_) {}
        const error = new Error(message);
        error.httpStatus = response.status;
        throw error;
      }
      data = await response.json();
      if (response.headers?.get?.('X-Clinical-Offline') === '1') source = 'offline';
    } catch (error) {
      if (error.httpStatus && error.httpStatus !== 503) throw error;
      data = await policyOffline(policyName);
      source = 'offline';
    }
    loader.classList.add('hidden');
    const sourceNotice = source === 'offline'
      ? '<div class="col-span-full bg-amber-950/30 border border-amber-700/50 p-3 rounded-xl text-amber-200 text-xs">Modo offline: diretrizes fornecidas pela base local empacotada nesta versão. Links/PDFs externos podem exigir conexão.</div>'
      : '';
    container.innerHTML = sourceNotice + data.items.map(item => {
      const sourceUrl = safeExternalUrl(item.source_url);
      const sourceLink = sourceUrl
        ? `<a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer" class="text-teal-300 hover:text-teal-200 underline underline-offset-2">${escapeHtml(item.source_title)}</a>`
        : `<span>${escapeHtml(item.source_title)}</span>`;
      return `
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 shadow-lg hover:border-slate-700 transition flex flex-col justify-between">
        <div class="space-y-2">
          <div class="flex items-center justify-between gap-2">
            <span class="px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20 text-[10px] font-bold uppercase tracking-wider">${escapeHtml(item.policy_name || policyName)}</span>
            <span class="text-[11px] text-slate-400 font-medium">${escapeHtml(item.target_demographic)}</span>
          </div>
          <h4 class="text-sm font-bold text-white tracking-tight">${escapeHtml(item.directive)}</h4>
          <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(item.clinical_guideline)}</p>
        </div>
        <div class="pt-3 mt-1 border-t border-slate-800 text-[11px] text-slate-500 leading-relaxed">
          <div><span class="font-semibold text-slate-400">Fonte:</span> ${sourceLink}</div>
          ${item.source_version ? `<div><span class="font-semibold text-slate-400">Versão:</span> ${escapeHtml(item.source_version)}</div>` : ''}
          ${item.source_page ? `<div><span class="font-semibold text-slate-400">Localizador:</span> ${escapeHtml(item.source_page)}</div>` : ''}
          <div><span class="font-semibold text-slate-400">Evidência:</span> ${escapeHtml(item.evidence_level || 'policy_level')}</div>
          <div><span class="font-semibold text-slate-400">Revisão clínica:</span> ${escapeHtml(item.last_clinical_review)} · <span class="uppercase">${escapeHtml(item.status)}</span></div>
        </div>
      </div>`;
    }).join('');
  } catch (err) {
    loader.classList.add('hidden');
    container.innerHTML = `<div class="col-span-full bg-rose-950/30 border border-rose-800/50 p-4 rounded-xl text-rose-300 text-sm text-center">${escapeHtml(err.message)}</div>`;
  }
}

function calculateDrip(e) {
  e.preventDefault();
  const v = Number.parseFloat(document.getElementById('drip-v').value);
  const t = Number.parseFloat(document.getElementById('drip-t').value);
  const u = document.getElementById('drip-u').value;
  if (!isPositiveFinite(v, t)) return showError('drip-result', 'Volume e tempo devem ser maiores que zero.');

  const minutes = u === 'h' ? t * 60 : t;
  const gotas = (v * DRIP_FACTORS.macro) / minutes;
  const micro = (v * DRIP_FACTORS.micro) / minutes;

  if (!isPositiveFinite(gotas, micro)) {
    return showError('drip-result', 'Não foi possível calcular um fluxo válido.');
  }

  const macroDisplay = formatPositiveMeasurement(gotas);
  const microDisplay = formatPositiveMeasurement(micro);
  const lowFlow = gotas < 1 || micro < 1;

  const res = document.getElementById('drip-result');
  res.classList.remove('hidden');
  res.innerHTML = `
    <div class="grid grid-cols-2 text-center divide-x divide-slate-800">
      <div>
        <p class="text-[10px] font-semibold text-slate-400 uppercase">Gotas/min · equipo ${DRIP_FACTORS.macro} gotas/mL</p>
        <p class="text-2xl font-bold text-cyan-400">${macroDisplay}</p>
      </div>
      <div>
        <p class="text-[10px] font-semibold text-slate-400 uppercase">Microgotas/min · equipo ${DRIP_FACTORS.micro} microgotas/mL</p>
        <p class="text-2xl font-bold text-cyan-400">${microDisplay}</p>
      </div>
    </div>
    ${lowFlow ? '<p class="text-[11px] text-amber-300 mt-3">Fluxo matemático positivo inferior a 1 gota/min em pelo menos um fator. Não arredonde para zero; confirme o equipo e avalie dispositivo de infusão apropriado.</p>' : ''}
  `;
}

const DOSE_UNITS = {
  mcg: { group: 'mass', factor: 0.001 },
  mg: { group: 'mass', factor: 1 },
  g: { group: 'mass', factor: 1000 },
  UI: { group: 'UI', factor: 1 },
  mEq: { group: 'mEq', factor: 1 },
};

function calculateMeds(e) {
  e.preventDefault();
  const presc = Number.parseFloat(document.getElementById('med-presc').value);
  const disp = Number.parseFloat(document.getElementById('med-disp').value);
  const vol = Number.parseFloat(document.getElementById('med-vol').value);
  const prescUnit = document.getElementById('med-presc-unit').value;
  const dispUnit = document.getElementById('med-disp-unit').value;
  if (!isPositiveFinite(presc, disp, vol)) return showError('med-result', 'Dose prescrita, dose disponível e volume devem ser maiores que zero.');

  const prescribedDef = DOSE_UNITS[prescUnit];
  const availableDef = DOSE_UNITS[dispUnit];
  if (!prescribedDef || !availableDef || prescribedDef.group !== availableDef.group) {
    return showError('med-result', 'As unidades da dose prescrita e da dose disponível precisam ser compatíveis.');
  }

  const prescribedBase = presc * prescribedDef.factor;
  const availableBase = disp * availableDef.factor;
  const result = (prescribedBase * vol) / availableBase;
  if (!isPositiveFinite(result)) return showError('med-result', 'Não foi possível calcular um volume válido.');

  const resultDisplay = formatPositiveMeasurement(result);
  const belowDisplayThreshold = result < 0.001;

  const res = document.getElementById('med-result');
  res.classList.remove('hidden');
  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">Volume calculado</p>
    <p class="text-2xl font-bold text-rose-400">${resultDisplay} mL</p>
    ${belowDisplayThreshold ? '<p class="text-[11px] text-amber-300 mt-2">O resultado matemático é positivo e inferior a 0,001 mL. Não interprete nem arredonde como zero; confirme concentração, apresentação e dispositivo de medida antes da administração.</p>' : ''}
    <p class="text-[11px] text-slate-400 mt-2">Confirme concentração, apresentação, via e limites de dose antes da administração.</p>
  `;
}

function calculateBMI(e) {
  e.preventDefault();
  const w = Number.parseFloat(document.getElementById('bmi-w').value);
  const h = Number.parseFloat(document.getElementById('bmi-h').value);
  const age = Number.parseInt(document.getElementById('bmi-age').value, 10);
  if (!isPositiveFinite(w, h) || !Number.isInteger(age) || age < 0 || age > 120) {
    return showError('bmi-result', 'Informe peso, altura e idade válidos.');
  }

  const bmi = w / (h * h);
  if (!Number.isFinite(bmi)) return showError('bmi-result', 'Não foi possível calcular um IMC válido.');

  const res = document.getElementById('bmi-result');
  res.classList.remove('hidden');
  if (age < 20) {
    res.innerHTML = `
      <p class="text-[10px] font-semibold text-amber-300 uppercase">Classificação pediátrica não calculada</p>
      <p class="text-2xl font-bold text-emerald-400 mt-1">${bmi.toFixed(1)} kg/m²</p>
      <p class="text-sm text-slate-300 mt-1">Em crianças e adolescentes, a interpretação exige idade e sexo com curvas/percentis apropriados; os cortes de adultos não são aplicáveis.</p>
    `;
    return;
  }

  let classification = '';
  if (age >= 60) {
    if (bmi <= 22) classification = 'Baixo peso (risco nutricional)';
    else if (bmi < 27) classification = 'Adequado (eutrófico)';
    else classification = 'Sobrepeso';
  } else {
    if (bmi < 18.5) classification = 'Abaixo do peso';
    else if (bmi < 25) classification = 'Peso normal';
    else if (bmi < 30) classification = 'Sobrepeso';
    else classification = 'Obesidade';
  }

  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">Tabela aplicada: ${age >= 60 ? 'idoso' : 'adulto'}</p>
    <p class="text-2xl font-bold text-emerald-400 mt-1">${bmi.toFixed(1)} kg/m²</p>
    <p class="text-sm font-medium text-white">${escapeHtml(classification)}</p>
  `;
}

function calculatePed(e) {
  e.preventDefault();
  const w = Number.parseFloat(document.getElementById('ped-w').value);
  if (!isPositiveFinite(w) || w > 200) return showError('ped-result', 'Informe um peso pediátrico válido.');

  let vol = 0;
  if (w <= 10) vol = w * 100;
  else if (w <= 20) vol = 1000 + ((w - 10) * 50);
  else vol = 1500 + ((w - 20) * 20);

  const mlPerHour = vol / 24;
  const res = document.getElementById('ped-result');
  res.classList.remove('hidden');
  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">Volume basal de manutenção</p>
    <p class="text-xl font-bold text-sky-400">${vol.toFixed(0)} mL / 24h</p>
    <hr class="border-slate-800 my-2">
    <p class="text-[10px] font-semibold text-slate-400 uppercase">Velocidade média</p>
    <p class="text-lg font-bold text-white">${mlPerHour.toFixed(1)} mL/h</p>
    <p class="text-[11px] text-slate-400 mt-2">Estimativa de manutenção; necessidades reais variam com idade, estado clínico, perdas, eletrólitos e comorbidades.</p>
  `;
}

function calculateCrCl(e) {
  e.preventDefault();
  const age = Number.parseInt(document.getElementById('crcl-age').value, 10);
  const w = Number.parseFloat(document.getElementById('crcl-w').value);
  const cr = Number.parseFloat(document.getElementById('crcl-cr').value);
  const sex = document.getElementById('crcl-sex').value;
  if (!Number.isInteger(age) || age < 18 || age > 120 || !isPositiveFinite(w, cr)) {
    return showError('crcl-result', 'Cockcroft-Gault requer idade adulta, peso e creatinina sérica válidos.');
  }

  let crcl = ((140 - age) * w) / (72 * cr);
  if (sex === 'F') crcl *= 0.85;
  if (!isPositiveFinite(crcl)) return showError('crcl-result', 'Não foi possível calcular um clearance válido.');

  const res = document.getElementById('crcl-result');
  res.classList.remove('hidden');
  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">Clearance de creatinina estimado (Cockcroft-Gault)</p>
    <p class="text-2xl font-bold text-amber-400 mt-1">${crcl.toFixed(1)} mL/min</p>
    <p class="text-[11px] text-slate-400 mt-2">Não é equivalente à TFG/eGFR. A escolha do peso e a aplicabilidade da fórmula dependem do contexto clínico.</p>
  `;
}

function calculateNaegele(e) {
  e.preventDefault();
  const dumStr = document.getElementById('dum-input').value;
  if (!dumStr) return showError('naegele-result', 'Informe a data da última menstruação.');

  const [year, month, day] = dumStr.split('-').map(Number);
  const dumDate = new Date(year, month - 1, day, 12, 0, 0, 0);
  if (Number.isNaN(dumDate.getTime())) return showError('naegele-result', 'DUM inválida.');

  const today = new Date();
  today.setHours(12, 0, 0, 0);
  const diffDays = Math.floor((today - dumDate) / 86400000);
  if (diffDays < 0) return showError('naegele-result', 'A DUM não pode estar no futuro.');
  if (diffDays > 315) return showError('naegele-result', 'A DUM informada resulta em idade gestacional acima de 45 semanas; confirme a data e a datação obstétrica.');

  const dppDate = new Date(dumDate);
  dppDate.setDate(dppDate.getDate() + 280);
  const weeks = Math.floor(diffDays / 7);
  const days = diffDays % 7;

  const res = document.getElementById('naegele-result');
  res.classList.remove('hidden');
  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">Data provável do parto</p>
    <p class="text-xl font-bold text-pink-400">${dppDate.toLocaleDateString('pt-BR')}</p>
    <p class="text-sm text-white mt-1">IG pela DUM hoje: <span class="font-bold">${weeks} sem e ${days} dias</span></p>
    <p class="text-[11px] text-slate-400 mt-2">Estimativa baseada em DUM; confirme com critérios obstétricos apropriados, especialmente quando a DUM for incerta ou o ciclo for irregular.</p>
  `;
}

function calculateMcDonald(e) {
  e.preventDefault();
  const au = Number.parseFloat(document.getElementById('au-input').value);
  if (!Number.isFinite(au) || au < 10 || au > 45) {
    return showError('mcdonald-result', 'Informe uma altura uterina entre 10 e 45 cm.');
  }

  const totalDays = Math.round(((au * 8) / 7) * 7);
  const weeks = Math.floor(totalDays / 7);
  const days = totalDays % 7;
  const res = document.getElementById('mcdonald-result');
  res.classList.remove('hidden');
  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">Estimativa histórica pela regra de McDonald</p>
    <p class="text-xl font-bold text-indigo-400">${weeks} sem e ${days} dias</p>
    <p class="text-[11px] text-slate-400 mt-2">A altura uterina é principalmente uma medida de acompanhamento do crescimento uterino/fetal e não deve substituir a datação obstétrica adequada.</p>
  `;
}


let lastNews2Result = null;
let lastNews2Source = null;


function renderNews2Result(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'news2-result'
    );

  if (!res || !result) return;


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  const aggregate =
    result[`aggregate_label_${suffix}`];

  const trigger =
    result[`trigger_label_${suffix}`];

  const monitoring =
    result[`monitoring_${suffix}`];

  const response =
    result[`response_${suffix}`];

  const judgement =
    result[
      `clinical_judgement_note_${suffix}`
    ];


  const components = [
    [
      'RR',
      result.components.respiration_rate
    ],

    [
      'SpO₂',
      result.components.spo2
    ],

    [
      'O₂',
      result.components.supplemental_oxygen
    ],

    [
      'SBP',
      result.components.systolic_bp
    ],

    [
      'Pulse',
      result.components.pulse
    ],

    [
      'ACVPU',
      result.components.consciousness
    ],

    [
      'Temp',
      result.components.temperature
    ]
  ];


  const offlineNotice =
    source === 'offline'
      ? `<p class="text-[11px] text-amber-300 mt-3">${escapeHtml(
          globalThis.ClinicalI18n
            ?.t?.('news2.offline')
          || clinicalText(
            'Resultado calculado localmente em modo offline.',
            'Result calculated locally while offline.'
          )
        )}</p>`
      : '';


  res.classList.remove(
    'hidden'
  );


  res.innerHTML = `
    <div class="flex flex-wrap items-end justify-between gap-4">

      <div>
        <p class="text-[10px] font-semibold text-slate-400 uppercase">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('news2.result')
            || clinicalText(
              'Pontuação NEWS2',
              'NEWS2 score'
            )
          )}
        </p>

        <p class="text-4xl font-black text-white">
          ${escapeHtml(result.total)}
        </p>

        <p class="text-sm font-semibold text-red-300">
          ${escapeHtml(aggregate)}
        </p>

        <p class="text-xs text-amber-200 mt-1">
          ${escapeHtml(trigger)}
        </p>
      </div>

      <div class="grid grid-cols-7 gap-1 text-center">
        ${components.map(
          ([label, value]) => `
            <div class="rounded bg-slate-900 px-2 py-1">
              <div class="text-[9px] text-slate-500">
                ${escapeHtml(label)}
              </div>
              <div class="text-sm font-bold text-slate-100">
                ${escapeHtml(value)}
              </div>
            </div>
          `
        ).join('')}
      </div>

    </div>

    <div class="mt-4 space-y-3 text-xs">

      <div>
        <span class="font-semibold text-slate-400">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('news2.monitoring')
            || clinicalText(
              'Monitorização',
              'Monitoring'
            )
          )}:
        </span>
        <span class="text-slate-200">
          ${escapeHtml(monitoring)}
        </span>
      </div>

      <div>
        <span class="font-semibold text-slate-400">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('news2.response')
            || clinicalText(
              'Resposta clínica',
              'Clinical response'
            )
          )}:
        </span>
        <span class="text-slate-200">
          ${escapeHtml(response)}
        </span>
      </div>

      <p class="text-[11px] text-slate-400">
        ${escapeHtml(judgement)}
      </p>

    </div>

    ${offlineNotice}
  `;
}


async function calculateNews2(event) {
  event.preventDefault();


  const payload = {
    respiration_rate:
      Number.parseInt(
        document.getElementById(
          'news2-rr'
        ).value,
        10
      ),

    spo2:
      Number.parseInt(
        document.getElementById(
          'news2-spo2'
        ).value,
        10
      ),

    spo2_scale:
      Number.parseInt(
        document.getElementById(
          'news2-scale'
        ).value,
        10
      ),

    scale2_prescribed:
      document.getElementById(
        'news2-scale2-prescribed'
      ).checked,

    supplemental_oxygen:
      document.getElementById(
        'news2-oxygen'
      ).checked,

    systolic_bp:
      Number.parseInt(
        document.getElementById(
          'news2-sbp'
        ).value,
        10
      ),

    pulse:
      Number.parseInt(
        document.getElementById(
          'news2-pulse'
        ).value,
        10
      ),

    consciousness:
      document.getElementById(
        'news2-consciousness'
      ).value,

    temperature:
      Number.parseFloat(
        document.getElementById(
          'news2-temp'
        ).value
      )
  };


  const numeric = [
    payload.respiration_rate,
    payload.spo2,
    payload.systolic_bp,
    payload.pulse,
    payload.temperature
  ];


  if (
    !numeric.every(
      Number.isFinite
    )
  ) {
    return showError(
      'news2-result',

      globalThis.ClinicalI18n
        ?.t?.('news2.invalid')
      || clinicalText(
        'Parâmetros NEWS2 inválidos.',
        'Invalid NEWS2 parameters.'
      )
    );
  }


  if (
    payload.spo2_scale === 2
    && !payload.scale2_prescribed
  ) {
    return showError(
      'news2-result',

      globalThis.ClinicalI18n
        ?.t?.('news2.scale2Required')
      || clinicalText(
        'A Escala 2 exige alvo 88–92% definido sob direção clínica qualificada.',
        'Scale 2 requires an 88–92% target set under qualified clinical direction.'
      )
    );
  }


  let result;
  let source = 'api';


  try {
    const apiResponse = await fetch(
      '/api/v1/tools/news2',
      {
        method: 'POST',

        headers: {
          'Content-Type':
            'application/json'
        },

        body:
          JSON.stringify(payload)
      }
    );


    if (!apiResponse.ok) {
      let detail =
        clinicalText(
          'Não foi possível calcular o NEWS2.',
          'Unable to calculate NEWS2.'
        );

      try {
        detail =
          (await apiResponse.json())
            .detail
          || detail;
      } catch (_) {}


      const error =
        new Error(detail);

      error.httpStatus =
        apiResponse.status;

      throw error;
    }


    result =
      await apiResponse.json();

  } catch (error) {

    if (error.httpStatus) {
      return showError(
        'news2-result',
        error.message
      );
    }


    try {
      result =
        globalThis.ClinicalTools
          .calculateNews2(
            payload
          );

      source = 'offline';

    } catch (_) {
      return showError(
        'news2-result',

        globalThis.ClinicalI18n
          ?.t?.('news2.invalid')
        || clinicalText(
          'Não foi possível calcular o NEWS2.',
          'Unable to calculate NEWS2.'
        )
      );
    }
  }


  lastNews2Result =
    result;

  lastNews2Source =
    source;


  renderNews2Result(
    result,
    source
  );
}



let lastEgfrResult = null;
let lastEgfrSource = null;

let lastCkdResult = null;
let lastCkdSource = null;

let lastAkiResult = null;
let lastAkiSource = null;


function nullableClinicalNumber(id) {
  const value =
    document.getElementById(id)?.value;

  if (
    value === ''
    || value === null
    || value === undefined
  ) {
    return null;
  }

  const parsed =
    Number.parseFloat(value);

  return Number.isFinite(parsed)
    ? parsed
    : null;
}


async function runClinicalCalculator(
  url,
  payload,
  offlineCalculator
) {
  try {
    const response = await fetch(
      url,
      {
        method: 'POST',

        headers: {
          'Content-Type':
            'application/json'
        },

        body:
          JSON.stringify(payload)
      }
    );


    if (!response.ok) {
      let detail =
        clinicalText(
          'Não foi possível calcular o resultado.',
          'Unable to calculate the result.'
        );

      try {
        const body =
          await response.json();

        detail =
          body.detail
          || detail;

      } catch (_) {}


      const error =
        new Error(detail);

      error.httpStatus =
        response.status;

      throw error;
    }


    return {
      result:
        await response.json(),

      source: 'api'
    };

  } catch (error) {
    if (error.httpStatus) {
      throw error;
    }

    return {
      result:
        await offlineCalculator(payload),

      source: 'offline'
    };
  }
}


function renalOfflineNotice(source) {
  if (source !== 'offline') {
    return '';
  }

  return `
    <p class="text-[11px] text-amber-300 mt-3">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('renal.offline')
        || clinicalText(
          'Resultado calculado localmente em modo offline.',
          'Result calculated locally while offline.'
        )
      )}
    </p>
  `;
}


function renderEgfrResult(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'renal-egfr-result'
    );

  if (!res || !result) return;


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  res.classList.remove('hidden');


  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('renal.result')
        || clinicalText(
          'Resultado',
          'Result'
        )
      )}
    </p>

    <p class="text-2xl font-bold text-teal-300 mt-1">
      ${escapeHtml(
        result.egfr_ml_min_1_73m2.toFixed(1)
      )}
      <span class="text-xs text-slate-400">
        mL/min/1.73 m²
      </span>
    </p>

    <p class="text-sm font-semibold text-white mt-1">
      ${escapeHtml(result.gfr_category)}
      ·
      ${escapeHtml(
        result[
          `gfr_category_label_${suffix}`
        ]
      )}
    </p>

    <p class="text-[11px] text-slate-400 mt-2">
      ${escapeHtml(
        result[
          `interpretation_${suffix}`
        ]
      )}
    </p>

    <p class="text-[10px] text-cyan-300 mt-3">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('renal.egfrBrazilAlignment')
        || clinicalText(
          'Brasil: CKD-EPI 2021 sem coeficiente de raça está alinhada ao consenso SBN/SBPC-ML 2024; a errata brasileira de 2025 confirma o expoente -1,200 já implementado.',
          'Brazil: race-free CKD-EPI 2021 aligns with the 2024 SBN/SBPC-ML consensus; the 2025 Brazilian erratum confirms the -1.200 exponent already implemented.'
        )
      )}
    </p>

    ${renalOfflineNotice(source)}
  `;
}


async function calculateEgfrTool(event) {
  event.preventDefault();


  const payload = {
    age_years:
      Number.parseInt(
        document.getElementById(
          'renal-egfr-age'
        ).value,
        10
      ),

    sex:
      document.getElementById(
        'renal-egfr-sex'
      ).value,

    serum_creatinine:
      Number.parseFloat(
        document.getElementById(
          'renal-egfr-cr'
        ).value
      ),

    creatinine_unit:
      document.getElementById(
        'renal-egfr-unit'
      ).value
  };


  if (
    !Number.isInteger(
      payload.age_years
    )
    || payload.age_years < 18
    || payload.age_years > 120
    || !Number.isFinite(
      payload.serum_creatinine
    )
    || payload.serum_creatinine <= 0
    || ![
      'female',
      'male'
    ].includes(payload.sex)
  ) {
    return showError(
      'renal-egfr-result',

      globalThis.ClinicalI18n
        ?.t?.('renal.invalidEgfr')
      || clinicalText(
        'Informe dados válidos para TFGe.',
        'Enter valid eGFR data.'
      )
    );
  }


  try {
    const {
      result,
      source
    } = await runClinicalCalculator(
      '/api/v1/tools/egfr-ckd-epi-2021',
      payload,
      globalThis.ClinicalTools
        .calculateEgfrCkdEpi2021
    );


    lastEgfrResult =
      result;

    lastEgfrSource =
      source;


    const ckdInput =
      document.getElementById(
        'renal-ckd-egfr'
      );

    if (ckdInput) {
      ckdInput.value =
        result.egfr_ml_min_1_73m2
          .toFixed(1);
    }


    renderEgfrResult(
      result,
      source
    );

  } catch (error) {
    showError(
      'renal-egfr-result',
      error.message
    );
  }
}


function renderCkdResult(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'renal-ckd-result'
    );

  if (!res || !result) return;


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  const status =
    result[
      `ckd_status_${suffix}`
    ];


  const note =
    result[
      `classification_note_${suffix}`
    ];


  const br =
    result.brazil_pcdt_context
    || null;


  const brStage =
    br?.pcdt_stage
      ? (
          br[
            `pcdt_stage_label_${suffix}`
          ]
          || br.pcdt_stage
        )
      : clinicalText(
          'Estágio não atribuído',
          'Stage not assigned'
        );


  const brAcr =
    br?.pcdt_acr_category
    || '—';


  const brStatus =
    br?.[
      `pcdt_ckd_status_${suffix}`
    ]
    || '';


  const brStageNote =
    br?.[
      `pcdt_stage_note_${suffix}`
    ]
    || '';


  const brAcrNote =
    br?.[
      `pcdt_acr_note_${suffix}`
    ]
    || '';


  const internationalTitle =
    globalThis.ClinicalI18n
      ?.t?.('renal.internationalTitle')
    || clinicalText(
      'Internacional · KDIGO 2024',
      'International · KDIGO 2024'
    );


  const brazilTitle =
    globalThis.ClinicalI18n
      ?.t?.('renal.brazilTitle')
    || clinicalText(
      'Brasil · SUS PCDT DRC 2024/2025',
      'Brazil · SUS CKD PCDT 2024/2025'
    );


  const pcdtStageLabel =
    globalThis.ClinicalI18n
      ?.t?.('renal.pcdtStage')
    || clinicalText(
      'Estágio SUS PCDT',
      'SUS PCDT stage'
    );


  const pcdtAcrLabel =
    globalThis.ClinicalI18n
      ?.t?.('renal.pcdtAcr')
    || clinicalText(
      'RAC SUS PCDT',
      'SUS PCDT ACR'
    );


  const equationBlocked =
    globalThis.ClinicalI18n
      ?.t?.('renal.pcdtEquationBlocked')
    || clinicalText(
      'A equação impressa no PCDT não é executada por conflitos de fonte verificados; nenhum dado de raça ou ancestralidade é usado.',
      'The equation printed in the PCDT is not executed because of verified source conflicts; no race or ancestry input is used.'
    );


  res.classList.remove('hidden');


  res.innerHTML = `
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">

      <div class="rounded-xl border border-emerald-900/60 bg-slate-950/60 p-3">
        <p class="text-[10px] font-semibold text-emerald-300 uppercase">
          ${escapeHtml(
            internationalTitle
          )}
        </p>

        <p class="text-2xl font-bold text-emerald-400 mt-1">
          ${escapeHtml(
            result.ga_classification
          )}
        </p>

        <p class="text-sm text-white mt-1">
          ${escapeHtml(status)}
        </p>

        <p class="text-[11px] text-slate-400 mt-2">
          ${escapeHtml(note)}
        </p>
      </div>

      <div class="rounded-xl border border-cyan-900/60 bg-slate-950/60 p-3">
        <p class="text-[10px] font-semibold text-cyan-300 uppercase">
          ${escapeHtml(
            brazilTitle
          )}
        </p>

        <p class="text-lg font-bold text-cyan-300 mt-1">
          ${escapeHtml(
            pcdtStageLabel
          )}:
          ${escapeHtml(
            brStage
          )}
        </p>

        <p class="text-xs text-white mt-1">
          ${escapeHtml(
            pcdtAcrLabel
          )}:
          ${escapeHtml(
            brAcr
          )}
        </p>

        ${
          brStatus
            ? `
              <p class="text-sm text-white mt-2">
                ${escapeHtml(
                  brStatus
                )}
              </p>
            `
            : ''
        }

        ${
          brStageNote
            ? `
              <p class="text-[11px] text-slate-400 mt-2">
                ${escapeHtml(
                  brStageNote
                )}
              </p>
            `
            : ''
        }

        ${
          brAcrNote
            ? `
              <p class="${
                br?.pcdt_acr_exact_300_ambiguous
                  ? 'text-[11px] text-amber-300 mt-2'
                  : 'text-[11px] text-slate-400 mt-2'
              }">
                ${escapeHtml(
                  brAcrNote
                )}
              </p>
            `
            : ''
        }

        <p class="text-[10px] text-amber-300 mt-3">
          ${escapeHtml(
            equationBlocked
          )}
        </p>
      </div>

    </div>

    ${renalOfflineNotice(source)}
  `;
}


async function calculateCkdTool(event) {
  event.preventDefault();


  const egfr =
    Number.parseFloat(
      document.getElementById(
        'renal-ckd-egfr'
      ).value
    );


  const acr =
    nullableClinicalNumber(
      'renal-ckd-acr'
    );


  if (
    !Number.isFinite(egfr)
    || egfr < 0
    || (
      acr !== null
      && acr < 0
    )
  ) {
    return showError(
      'renal-ckd-result',

      globalThis.ClinicalI18n
        ?.t?.('renal.invalidCkd')
      || clinicalText(
        'Informe dados válidos para classificação renal.',
        'Enter valid kidney-classification data.'
      )
    );
  }


  const payload = {
    egfr_ml_min_1_73m2:
      egfr,

    acr,

    acr_unit:
      document.getElementById(
        'renal-ckd-acr-unit'
      ).value,

    chronicity_at_least_3_months:
      document.getElementById(
        'renal-ckd-chronicity'
      ).checked,

    other_kidney_damage_marker:
      document.getElementById(
        'renal-ckd-other-marker'
      ).checked,

    on_dialysis:
      document.getElementById(
        'renal-ckd-dialysis'
      ).checked
  };


  try {
    const {
      result,
      source
    } = await runClinicalCalculator(
      '/api/v1/tools/ckd-classification',
      payload,
      globalThis.ClinicalTools
        .classifyCkd
    );


    lastCkdResult =
      result;

    lastCkdSource =
      source;


    renderCkdResult(
      result,
      source
    );

  } catch (error) {
    showError(
      'renal-ckd-result',
      error.message
    );
  }
}


function renderAkiResult(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'renal-aki-result'
    );

  if (!res || !result) return;


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  const interpretation =
    result[
      `interpretation_${suffix}`
    ];


  const criteria =
    result[
      `criteria_${suffix}`
    ] || [];


  const stageLabel =
    result.stage === null
      ? clinicalText(
          'Não classificável',
          'Not classifiable'
        )
      : clinicalText(
          `KDIGO estágio ${result.stage}`,
          `KDIGO stage ${result.stage}`
        );


  const urineRate =
    result.urine_output_ml_kg_h;


  res.classList.remove('hidden');


  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">
      KDIGO AKI
    </p>

    <p class="text-2xl font-bold text-amber-300 mt-1">
      ${escapeHtml(stageLabel)}
    </p>

    ${
      urineRate !== null
        ? `
          <p class="text-xs text-slate-300 mt-1">
            ${escapeHtml(
              clinicalText(
                'Diurese calculada',
                'Calculated urine output'
              )
            )}:
            ${escapeHtml(
              urineRate.toFixed(4)
            )}
            mL/kg/h
          </p>
        `
        : ''
    }

    ${
      criteria.length
        ? `
          <ul class="mt-3 space-y-1">
            ${criteria.map(
              item => `
                <li class="text-[11px] text-slate-300">
                  • ${escapeHtml(item)}
                </li>
              `
            ).join('')}
          </ul>
        `
        : ''
    }

    <p class="text-[11px] text-slate-400 mt-3">
      ${escapeHtml(interpretation)}
    </p>

    <p class="text-[10px] text-cyan-300 mt-3">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('renal.akiBrazilAlignment')
        || clinicalText(
          'Brasil: a Linha de Cuidado do Ministério da Saúde utiliza a classificação KDIGO 2012; não há segundo algoritmo numérico brasileiro.',
          'Brazil: the Ministry of Health care pathway uses KDIGO 2012 classification; there is no second Brazilian numerical algorithm.'
        )
      )}
    </p>

    ${renalOfflineNotice(source)}
  `;
}


async function calculateAkiTool(event) {
  event.preventDefault();


  const current =
    nullableClinicalNumber(
      'renal-aki-current'
    );

  const baseline =
    nullableClinicalNumber(
      'renal-aki-baseline'
    );

  const interval =
    nullableClinicalNumber(
      'renal-aki-interval'
    );

  const weight =
    nullableClinicalNumber(
      'renal-aki-weight'
    );

  const urine =
    nullableClinicalNumber(
      'renal-aki-urine'
    );

  const urineHours =
    nullableClinicalNumber(
      'renal-aki-urine-hours'
    );

  const anuria =
    nullableClinicalNumber(
      'renal-aki-anuria'
    );


  if (
    baseline !== null
    && current === null
  ) {
    return showError(
      'renal-aki-result',

      globalThis.ClinicalI18n
        ?.t?.(
          'renal.akiBaselineNeedsCurrent'
        )
      || clinicalText(
        'A creatinina basal exige creatinina atual.',
        'Baseline creatinine requires current creatinine.'
      )
    );
  }


  const urineCount = [
    weight,
    urine,
    urineHours
  ].filter(
    value => value !== null
  ).length;


  if (
    urineCount !== 0
    && urineCount !== 3
  ) {
    return showError(
      'renal-aki-result',

      globalThis.ClinicalI18n
        ?.t?.('renal.akiUrineGroup')
      || clinicalText(
        'Informe peso, diurese e duração conjuntamente.',
        'Provide weight, urine output and duration together.'
      )
    );
  }


  const payload = {
    current_creatinine:
      current,

    current_creatinine_unit:
      document.getElementById(
        'renal-aki-current-unit'
      ).value,

    baseline_creatinine:
      baseline,

    baseline_creatinine_unit:
      baseline === null
        ? null
        : document.getElementById(
            'renal-aki-baseline-unit'
          ).value,

    baseline_interval_hours:
      interval,

    weight_kg:
      weight,

    urine_output_ml:
      urine,

    urine_output_duration_hours:
      urineHours,

    anuria_duration_hours:
      anuria,

    renal_replacement_therapy:
      document.getElementById(
        'renal-aki-krt'
      ).checked
  };


  try {
    const {
      result,
      source
    } = await runClinicalCalculator(
      '/api/v1/tools/kdigo-aki',
      payload,
      globalThis.ClinicalTools
        .calculateKdigoAki
    );


    lastAkiResult =
      result;

    lastAkiSource =
      source;


    renderAkiResult(
      result,
      source
    );

  } catch (error) {
    showError(
      'renal-aki-result',
      error.message
    );
  }
}



let lastHemodynamicsResult = null;
let lastHemodynamicsSource = null;


function renderHemodynamicsResult(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'hemodynamics-result'
    );

  if (!res || !result) {
    return;
  }


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  const interpretation =
    result[
      `interpretation_${suffix}`
    ];


  const mapNote =
    result[
      `map_note_${suffix}`
    ];


  const offlineNotice =
    source === 'offline'
      ? `
        <p class="text-[11px] text-amber-300 mt-3">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('hemo.offline')
            || clinicalText(
              'Resultado calculado localmente em modo offline.',
              'Result calculated locally while offline.'
            )
          )}
        </p>
      `
      : '';


  const values = [
    [
      globalThis.ClinicalI18n
        ?.t?.('hemo.pp')
      || clinicalText(
        'Pressão de pulso',
        'Pulse pressure'
      ),
      `${result.pulse_pressure_mm_hg.toFixed(1)} mmHg`
    ],

    [
      globalThis.ClinicalI18n
        ?.t?.('hemo.map')
      || clinicalText(
        'Pressão arterial média',
        'Mean arterial pressure'
      ),
      `${result.mean_arterial_pressure_mm_hg.toFixed(1)} mmHg`
    ],

    [
      'Shock Index',
      result.shock_index.toFixed(3)
    ],

    [
      'Modified Shock Index',
      result.modified_shock_index.toFixed(3)
    ]
  ];


  res.classList.remove(
    'hidden'
  );


  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('hemo.result')
        || clinicalText(
          'Índices calculados',
          'Calculated indices'
        )
      )}
    </p>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
      ${values.map(
        ([label, value]) => `
          <div class="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p class="text-[10px] text-slate-400">
              ${escapeHtml(label)}
            </p>
            <p class="text-lg font-bold text-cyan-300 mt-1">
              ${escapeHtml(value)}
            </p>
          </div>
        `
      ).join('')}
    </div>

    <p class="text-[11px] text-slate-300 mt-4">
      ${escapeHtml(interpretation)}
    </p>

    <p class="text-[11px] text-slate-500 mt-2">
      ${escapeHtml(mapNote)}
    </p>

    ${offlineNotice}
  `;
}


async function calculateHemodynamicsTool(
  event
) {
  event.preventDefault();


  const payload = {
    systolic_bp:
      Number.parseFloat(
        document.getElementById(
          'hemo-sbp'
        ).value
      ),

    diastolic_bp:
      Number.parseFloat(
        document.getElementById(
          'hemo-dbp'
        ).value
      ),

    heart_rate:
      Number.parseFloat(
        document.getElementById(
          'hemo-hr'
        ).value
      )
  };


  if (
    !Number.isFinite(
      payload.systolic_bp
    )
    || payload.systolic_bp <= 0
    || !Number.isFinite(
      payload.diastolic_bp
    )
    || payload.diastolic_bp <= 0
    || !Number.isFinite(
      payload.heart_rate
    )
    || payload.heart_rate <= 0
    || payload.systolic_bp
      < payload.diastolic_bp
  ) {
    return showError(
      'hemodynamics-result',

      globalThis.ClinicalI18n
        ?.t?.('hemo.invalid')
      || clinicalText(
        'Informe PAS, PAD e frequência cardíaca válidas.',
        'Enter valid SBP, DBP and heart rate values.'
      )
    );
  }


  try {
    const {
      result,
      source
    } = await runClinicalCalculator(
      '/api/v1/tools/hemodynamics',
      payload,
      globalThis.ClinicalTools
        .calculateHemodynamics
    );


    lastHemodynamicsResult =
      result;

    lastHemodynamicsSource =
      source;


    renderHemodynamicsResult(
      result,
      source
    );

  } catch (error) {
    showError(
      'hemodynamics-result',
      error.message
    );
  }
}



let lastOxygenationResult = null;
let lastOxygenationSource = null;


function renderOxygenationResult(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'oxygenation-result'
    );

  if (!res || !result) {
    return;
  }


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  const interpretation =
    result[
      `interpretation_${suffix}`
    ];


  const sfNote =
    result[
      `sf_note_${suffix}`
    ];


  const fio2Note =
    result[
      `fio2_note_${suffix}`
    ];


  const ratios = [];


  if (
    result.pf_ratio_mm_hg
    !== null
  ) {
    ratios.push([
      globalThis.ClinicalI18n
        ?.t?.('oxygen.pf')
      || clinicalText(
        'Relação P/F',
        'P/F ratio'
      ),

      result.pf_ratio_mm_hg
        .toFixed(1)
    ]);
  }


  if (
    result.sf_ratio
    !== null
  ) {
    ratios.push([
      globalThis.ClinicalI18n
        ?.t?.('oxygen.sf')
      || clinicalText(
        'Relação S/F',
        'S/F ratio'
      ),

      result.sf_ratio
        .toFixed(1)
    ]);
  }


  const offlineNotice =
    source === 'offline'
      ? `
        <p class="text-[11px] text-amber-300 mt-3">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('oxygen.offline')
            || clinicalText(
              'Resultado calculado localmente em modo offline.',
              'Result calculated locally while offline.'
            )
          )}
        </p>
      `
      : '';


  const sfCaution =
    sfNote
      ? `
        <div class="mt-3 rounded-lg border border-slate-800 bg-slate-900 p-3">
          <p class="text-[10px] font-semibold text-amber-300 uppercase">
            ${escapeHtml(
              globalThis.ClinicalI18n
                ?.t?.('oxygen.sfCaution')
              || clinicalText(
                'Atenção à interpretação da relação S/F',
                'S/F ratio interpretation caution'
              )
            )}
          </p>

          <p class="text-[11px] text-slate-300 mt-1">
            ${escapeHtml(sfNote)}
          </p>
        </div>
      `
      : '';


  res.classList.remove(
    'hidden'
  );


  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('oxygen.result')
        || clinicalText(
          'Relações calculadas',
          'Calculated ratios'
        )
      )}
    </p>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
      ${ratios.map(
        ([label, value]) => `
          <div class="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p class="text-[10px] text-slate-400">
              ${escapeHtml(label)}
            </p>

            <p class="text-2xl font-bold text-sky-400 mt-1">
              ${escapeHtml(value)}
            </p>
          </div>
        `
      ).join('')}
    </div>

    <p class="text-[11px] text-slate-300 mt-4">
      ${escapeHtml(interpretation)}
    </p>

    ${sfCaution}

    <p class="text-[11px] text-slate-500 mt-3">
      ${escapeHtml(fio2Note)}
    </p>

    ${offlineNotice}
  `;
}


async function calculateOxygenationTool(
  event
) {
  event.preventDefault();


  const fio2 =
    Number.parseFloat(
      document.getElementById(
        'oxygen-fio2'
      ).value
    );


  const pao2 =
    nullableClinicalNumber(
      'oxygen-pao2'
    );


  const spo2 =
    nullableClinicalNumber(
      'oxygen-spo2'
    );


  if (
    !Number.isFinite(fio2)
    || fio2 < 21
    || fio2 > 100
    || (
      pao2 === null
      && spo2 === null
    )
    || (
      pao2 !== null
      && pao2 <= 0
    )
    || (
      spo2 !== null
      && (
        spo2 < 1
        || spo2 > 100
      )
    )
  ) {
    return showError(
      'oxygenation-result',

      globalThis.ClinicalI18n
        ?.t?.('oxygen.invalid')
      || clinicalText(
        'Informe FiO₂ e pelo menos PaO₂ ou SpO₂ válidas.',
        'Enter FiO₂ and at least one valid PaO₂ or SpO₂ value.'
      )
    );
  }


  const payload = {
    fio2_percent:
      fio2,

    pao2_mm_hg:
      pao2,

    spo2_percent:
      spo2
  };


  try {
    const {
      result,
      source
    } = await runClinicalCalculator(
      '/api/v1/tools/oxygenation',
      payload,
      globalThis.ClinicalTools
        .calculateOxygenation
    );


    lastOxygenationResult =
      result;

    lastOxygenationSource =
      source;


    renderOxygenationResult(
      result,
      source
    );

  } catch (error) {
    showError(
      'oxygenation-result',
      error.message
    );
  }
}



let lastMetabolicResult = null;
let lastMetabolicSource = null;


function renderMetabolicResult(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'metabolic-result'
    );

  if (!res || !result) {
    return;
  }


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  const values = [];


  if (
    result.anion_gap_meq_l
    !== null
  ) {
    values.push([
      globalThis.ClinicalI18n
        ?.t?.('metabolic.ag')
      || clinicalText(
        'Ânion gap',
        'Anion gap'
      ),

      `${result.anion_gap_meq_l.toFixed(1)} mEq/L`
    ]);
  }


  if (
    result.albumin_corrected_anion_gap_meq_l
    !== null
  ) {
    values.push([
      globalThis.ClinicalI18n
        ?.t?.('metabolic.correctedAg')
      || clinicalText(
        'Ânion gap corrigido',
        'Albumin-corrected anion gap'
      ),

      `${result.albumin_corrected_anion_gap_meq_l.toFixed(1)} mEq/L`
    ]);
  }


  if (
    result.calculated_osmolality_mosm_kg
    !== null
  ) {
    values.push([
      globalThis.ClinicalI18n
        ?.t?.('metabolic.osmolality')
      || clinicalText(
        'Osmolalidade calculada',
        'Calculated osmolality'
      ),

      `${result.calculated_osmolality_mosm_kg.toFixed(1)} mOsm/kg`
    ]);
  }


  if (
    result.corrected_sodium_meq_l
    !== null
  ) {
    values.push([
      globalThis.ClinicalI18n
        ?.t?.('metabolic.correctedNa')
      || clinicalText(
        'Sódio corrigido',
        'Corrected sodium'
      ),

      `${result.corrected_sodium_meq_l.toFixed(1)} mEq/L`
    ]);
  }


  const winterInterpretation =
    result[
      `winter_interpretation_${suffix}`
    ];


  const deltaInterpretation =
    result[
      `delta_interpretation_${suffix}`
    ];


  const validityNotes =
    result[
      `validity_notes_${suffix}`
    ] || [];


  const interpretation =
    result[
      `interpretation_${suffix}`
    ];


  const winterBlock =
    result.winter_analysis_applied
      ? `
        <div class="rounded-lg border border-slate-800 bg-slate-900 p-3">
          <p class="text-[10px] font-semibold text-slate-400 uppercase">
            ${escapeHtml(
              globalThis.ClinicalI18n
                ?.t?.('metabolic.winter')
              || clinicalText(
                'Compensação de Winter',
                'Winter compensation'
              )
            )}
          </p>

          <p class="text-lg font-bold text-cyan-300 mt-1">
            ${escapeHtml(
              result.winter_expected_paco2_mm_hg.toFixed(1)
            )}
            mmHg
            <span class="text-xs font-normal text-slate-400">
              (${escapeHtml(
                result.winter_lower_mm_hg.toFixed(1)
              )}–${escapeHtml(
                result.winter_upper_mm_hg.toFixed(1)
              )})
            </span>
          </p>

          ${
            winterInterpretation
              ? `
                <p class="text-[11px] text-slate-300 mt-2">
                  ${escapeHtml(
                    winterInterpretation
                  )}
                </p>
              `
              : ''
          }
        </div>
      `
      : '';


  const deltaBlock =
    result.delta_analysis_applied
      ? `
        <div class="rounded-lg border border-slate-800 bg-slate-900 p-3">
          <p class="text-[10px] font-semibold text-slate-400 uppercase">
            ${escapeHtml(
              globalThis.ClinicalI18n
                ?.t?.('metabolic.delta')
              || 'Delta ratio'
            )}
          </p>

          <p class="text-lg font-bold text-fuchsia-300 mt-1">
            ${escapeHtml(
              result.delta_ratio.toFixed(2)
            )}
          </p>

          ${
            deltaInterpretation
              ? `
                <p class="text-[11px] text-slate-300 mt-2">
                  ${escapeHtml(
                    deltaInterpretation
                  )}
                </p>
              `
              : ''
          }
        </div>
      `
      : '';


  const validityBlock =
    validityNotes.length
      ? `
        <div class="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
          <p class="text-[10px] font-semibold text-amber-300 uppercase">
            ${escapeHtml(
              globalThis.ClinicalI18n
                ?.t?.('metabolic.validity')
              || clinicalText(
                'Validade / limitações',
                'Validity / limitations'
              )
            )}
          </p>

          <ul class="mt-2 space-y-1">
            ${validityNotes.map(
              note => `
                <li class="text-[11px] text-slate-300">
                  • ${escapeHtml(note)}
                </li>
              `
            ).join('')}
          </ul>
        </div>
      `
      : '';


  const offlineNotice =
    source === 'offline'
      ? `
        <p class="text-[11px] text-amber-300 mt-3">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('metabolic.offline')
            || clinicalText(
              'Resultado calculado localmente em modo offline.',
              'Result calculated locally while offline.'
            )
          )}
        </p>
      `
      : '';


  res.classList.remove(
    'hidden'
  );


  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('metabolic.result')
        || clinicalText(
          'Resultados calculados',
          'Calculated results'
        )
      )}
    </p>

    ${
      values.length
        ? `
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
            ${values.map(
              ([label, value]) => `
                <div class="rounded-lg border border-slate-800 bg-slate-900 p-3">
                  <p class="text-[10px] text-slate-400">
                    ${escapeHtml(label)}
                  </p>

                  <p class="text-lg font-bold text-purple-300 mt-1">
                    ${escapeHtml(value)}
                  </p>
                </div>
              `
            ).join('')}
          </div>
        `
        : ''
    }

    ${
      winterBlock
      || deltaBlock
        ? `
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-4">
            ${winterBlock}
            ${deltaBlock}
          </div>
        `
        : ''
    }

    ${validityBlock}

    <p class="text-[11px] text-slate-400 mt-4">
      ${escapeHtml(interpretation)}
    </p>

    ${offlineNotice}
  `;
}


async function calculateMetabolicTool(
  event
) {
  event.preventDefault();


  const sodium =
    Number.parseFloat(
      document.getElementById(
        'metabolic-na'
      ).value
    );


  const chloride =
    nullableClinicalNumber(
      'metabolic-cl'
    );


  const bicarbonate =
    nullableClinicalNumber(
      'metabolic-hco3'
    );


  const albumin =
    nullableClinicalNumber(
      'metabolic-albumin'
    );


  const glucose =
    nullableClinicalNumber(
      'metabolic-glucose'
    );


  const bun =
    nullableClinicalNumber(
      'metabolic-bun'
    );


  const paco2 =
    nullableClinicalNumber(
      'metabolic-paco2'
    );


  const confirmed =
    document.getElementById(
      'metabolic-acidosis-confirmed'
    ).checked;


  if (
    !Number.isFinite(sodium)
    || sodium <= 0
  ) {
    return showError(
      'metabolic-result',

      globalThis.ClinicalI18n
        ?.t?.('metabolic.invalid')
      || clinicalText(
        'Informe um sódio válido.',
        'Enter a valid sodium value.'
      )
    );
  }


  if (
    (chloride === null)
    !== (bicarbonate === null)
  ) {
    return showError(
      'metabolic-result',

      globalThis.ClinicalI18n
        ?.t?.('metabolic.agPair')
      || clinicalText(
        'Cloreto e bicarbonato devem ser informados conjuntamente.',
        'Chloride and bicarbonate must be supplied together.'
      )
    );
  }


  if (
    albumin !== null
    && chloride === null
  ) {
    return showError(
      'metabolic-result',

      globalThis.ClinicalI18n
        ?.t?.('metabolic.albuminNeedsAg')
      || clinicalText(
        'A correção por albumina exige cloreto e bicarbonato.',
        'Albumin correction requires chloride and bicarbonate.'
      )
    );
  }


  if (
    bun !== null
    && glucose === null
  ) {
    return showError(
      'metabolic-result',

      globalThis.ClinicalI18n
        ?.t?.('metabolic.bunNeedsGlucose')
      || clinicalText(
        'BUN exige glicose para cálculo de osmolalidade.',
        'BUN requires glucose for calculated osmolality.'
      )
    );
  }


  if (
    chloride === null
    && glucose === null
  ) {
    return showError(
      'metabolic-result',

      globalThis.ClinicalI18n
        ?.t?.('metabolic.noPath')
      || clinicalText(
        'Informe cloreto+bicarbonato e/ou glicose.',
        'Provide chloride+bicarbonate and/or glucose.'
      )
    );
  }


  const optionalPositive = [
    chloride,
    bicarbonate,
    albumin,
    paco2
  ];


  if (
    optionalPositive.some(
      value =>
        value !== null
        && (
          !Number.isFinite(value)
          || value <= 0
        )
    )
    || (
      glucose !== null
      && (
        !Number.isFinite(glucose)
        || glucose < 0
      )
    )
    || (
      bun !== null
      && (
        !Number.isFinite(bun)
        || bun < 0
      )
    )
  ) {
    return showError(
      'metabolic-result',

      globalThis.ClinicalI18n
        ?.t?.('metabolic.invalid')
      || clinicalText(
        'Valores metabólicos inválidos.',
        'Invalid metabolic values.'
      )
    );
  }


  const payload = {
    sodium_meq_l:
      sodium,

    chloride_meq_l:
      chloride,

    bicarbonate_meq_l:
      bicarbonate,

    albumin_g_dl:
      albumin,

    glucose_mg_dl:
      glucose,

    bun_mg_dl:
      bun,

    paco2_mm_hg:
      paco2,

    metabolic_acidosis_confirmed:
      confirmed
  };


  try {
    const {
      result,
      source
    } = await runClinicalCalculator(
      '/api/v1/tools/acid-base-metabolic',
      payload,
      globalThis.ClinicalTools
        .calculateMetabolicToolkit
    );


    lastMetabolicResult =
      result;

    lastMetabolicSource =
      source;


    renderMetabolicResult(
      result,
      source
    );

  } catch (error) {
    showError(
      'metabolic-result',
      error.message
    );
  }
}



let lastGrowthResult = null;
let lastGrowthSource = null;


function growthIndicatorLabel(
  name
) {
  const keys = {
    weight_for_age:
      'growth.wfa',

    length_height_for_age:
      'growth.hfa',

    weight_for_length_height:
      'growth.wflh',

    bmi_for_age:
      'growth.bfa',

    head_circumference_for_age:
      'growth.hcfa'
  };


  const fallbacks = {
    weight_for_age: [
      'Peso para idade',
      'Weight for age'
    ],

    length_height_for_age: [
      'Comprimento / estatura para idade',
      'Length / height for age'
    ],

    weight_for_length_height: [
      'Peso para comprimento / estatura',
      'Weight for length / height'
    ],

    bmi_for_age: [
      'IMC para idade',
      'BMI for age'
    ],

    head_circumference_for_age: [
      'Perímetro cefálico para idade',
      'Head circumference for age'
    ]
  };


  const fallback =
    fallbacks[name]
    || [name, name];


  return (
    globalThis.ClinicalI18n
      ?.t?.(keys[name])
    || clinicalText(
      fallback[0],
      fallback[1]
    )
  );
}


function renderGrowthResult(
  result,
  source = 'api'
) {
  const res =
    document.getElementById(
      'growth-result'
    );


  if (!res || !result) {
    return;
  }


  const suffix =
    uiLanguage() === 'en-GB'
      ? 'en'
      : 'pt';


  const cards =
    Object.entries(
      result.indicators
      || {}
    )
      .filter(
        ([, value]) =>
          value !== null
      )
      .map(
        ([name, value]) => {
          const whoClass =
            value.classification_who;

          const brClass =
            value.classification_br;


          const whoText =
            whoClass
              ? whoClass[
                  `label_${suffix}`
                ]
              : (
                  globalThis.ClinicalI18n
                    ?.t?.(
                      'growth.noNamedClass'
                    )
                  || clinicalText(
                    'Sem classificação nominal adicional',
                    'No additional named classification'
                  )
                );


          const brText =
            brClass
              ? brClass[
                  `label_${suffix}`
                ]
              : (
                  globalThis.ClinicalI18n
                    ?.t?.(
                      'growth.noNamedClass'
                    )
                  || clinicalText(
                    'Sem classificação nominal adicional',
                    'No additional named classification'
                  )
                );


          const percentileText =
            value.percentile_available
            && value.percentile !== null
              ? `${value.percentile.toFixed(2)}%`
              : (
                  globalThis.ClinicalI18n
                    ?.t?.(
                      'growth.percentileUnavailable'
                    )
                  || clinicalText(
                    'Indisponível fora de ±3 DP',
                    'Unavailable outside ±3 SD'
                  )
                );


          const flag =
            value.plausibility_flag
              ? `
                <p class="text-[10px] text-red-300 mt-2">
                  ${escapeHtml(
                    clinicalText(
                      'Valor fora da faixa de plausibilidade WHO',
                      'Value outside the WHO plausibility range'
                    )
                  )}
                  ·
                  ${escapeHtml(
                    value.who_plausibility_range
                  )}
                </p>
              `
              : '';


          return `
            <div class="rounded-xl border border-slate-800 bg-slate-900 p-4 space-y-3">

              <p class="text-xs font-semibold text-white">
                ${escapeHtml(
                  growthIndicatorLabel(
                    name
                  )
                )}
              </p>

              <div class="grid grid-cols-2 gap-2">

                <div>
                  <p class="text-[10px] text-slate-500 uppercase">
                    ${escapeHtml(
                      globalThis.ClinicalI18n
                        ?.t?.('growth.z')
                      || 'Z'
                    )}
                  </p>

                  <p class="text-xl font-bold text-emerald-300">
                    ${escapeHtml(
                      value.z_score.toFixed(2)
                    )}
                  </p>
                </div>

                <div>
                  <p class="text-[10px] text-slate-500 uppercase">
                    ${escapeHtml(
                      globalThis.ClinicalI18n
                        ?.t?.(
                          'growth.percentile'
                        )
                      || clinicalText(
                        'Percentil',
                        'Percentile'
                      )
                    )}
                  </p>

                  <p class="text-sm font-semibold text-slate-200 mt-1">
                    ${escapeHtml(
                      percentileText
                    )}
                  </p>
                </div>

              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">

                <div class="rounded-lg bg-slate-950/70 p-2">
                  <p class="text-[10px] text-slate-500 uppercase">
                    ${escapeHtml(
                      globalThis.ClinicalI18n
                        ?.t?.('growth.who')
                      || 'WHO'
                    )}
                  </p>

                  <p class="text-[11px] text-slate-200 mt-1">
                    ${escapeHtml(
                      whoText
                    )}
                  </p>
                </div>

                <div class="rounded-lg bg-slate-950/70 p-2">
                  <p class="text-[10px] text-slate-500 uppercase">
                    ${escapeHtml(
                      globalThis.ClinicalI18n
                        ?.t?.('growth.brazil')
                      || 'Brasil · SISVAN'
                    )}
                  </p>

                  <p class="text-[11px] text-slate-200 mt-1">
                    ${escapeHtml(
                      brText
                    )}
                  </p>
                </div>

              </div>

              <p class="text-[9px] text-slate-600">
                ${escapeHtml(
                  value.reference_standard
                )}
              </p>

              ${flag}

            </div>
          `;
        }
      );


  const warnings =
    result[
      `warnings_${suffix}`
    ] || [];


  const warningBlock =
    warnings.length
      ? `
        <div class="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">

          <p class="text-[10px] font-semibold text-amber-300 uppercase">
            ${escapeHtml(
              globalThis.ClinicalI18n
                ?.t?.('growth.warning')
              || clinicalText(
                'Observações / alertas',
                'Notes / warnings'
              )
            )}
          </p>

          <ul class="mt-2 space-y-1">
            ${warnings.map(
              warning => `
                <li class="text-[11px] text-slate-300">
                  • ${escapeHtml(
                    warning
                  )}
                </li>
              `
            ).join('')}
          </ul>

        </div>
      `
      : '';


  const adjustmentBlock =
    result.measurement_adjustment_cm !== 0
      ? `
        <p class="text-[11px] text-cyan-300 mt-3">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('growth.adjustment')
            || clinicalText(
              'Ajuste de posição aplicado',
              'Measurement-position adjustment'
            )
          )}:
          ${escapeHtml(
            result.measurement_adjustment_cm
              .toFixed(1)
          )}
          cm
        </p>
      `
      : '';


  const bmiBlock =
    result.bmi_kg_m2 !== null
      ? `
        <p class="text-[11px] text-slate-400 mt-2">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('growth.bmi')
            || clinicalText(
              'IMC calculado',
              'Calculated BMI'
            )
          )}:
          ${escapeHtml(
            result.bmi_kg_m2
              .toFixed(4)
          )}
          kg/m²
        </p>
      `
      : '';


  const offlineBlock =
    source === 'offline'
      ? `
        <p class="text-[11px] text-amber-300 mt-3">
          ${escapeHtml(
            globalThis.ClinicalI18n
              ?.t?.('growth.offline')
            || clinicalText(
              'Resultado calculado localmente com as tabelas WHO precacheadas.',
              'Result calculated locally using the precached WHO tables.'
            )
          )}
        </p>
      `
      : '';


  res.classList.remove(
    'hidden'
  );


  res.innerHTML = `
    <p class="text-[10px] font-semibold text-slate-400 uppercase">
      ${escapeHtml(
        globalThis.ClinicalI18n
          ?.t?.('growth.results')
        || clinicalText(
          'Resultados de crescimento',
          'Growth results'
        )
      )}
    </p>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-3">
      ${cards.join('')}
    </div>

    ${adjustmentBlock}
    ${bmiBlock}
    ${warningBlock}
    ${offlineBlock}
  `;
}


async function calculateGrowthTool(
  event
) {
  event.preventDefault();


  const sex =
    document.getElementById(
      'growth-sex'
    ).value;


  const age =
    Number.parseFloat(
      document.getElementById(
        'growth-age'
      ).value
    );


  const ageUnit =
    document.getElementById(
      'growth-age-unit'
    ).value;


  const ageBasis =
    document.getElementById(
      'growth-age-basis'
    ).value;


  const weight =
    nullableClinicalNumber(
      'growth-weight'
    );


  const lenhei =
    nullableClinicalNumber(
      'growth-lenhei'
    );


  const head =
    nullableClinicalNumber(
      'growth-head'
    );


  const position =
    document.getElementById(
      'growth-position'
    ).value || null;


  const oedema =
    document.getElementById(
      'growth-oedema'
    ).checked;


  if (
    !['male', 'female'].includes(
      sex
    )
    || !Number.isFinite(age)
    || age < 0
    || (
      weight === null
      && lenhei === null
      && head === null
    )
  ) {
    return showError(
      'growth-result',

      globalThis.ClinicalI18n
        ?.t?.('growth.invalid')
      || clinicalText(
        'Informe sexo, idade válida e pelo menos uma medida antropométrica.',
        'Enter sex, a valid age and at least one anthropometric measurement.'
      )
    );
  }


  if (
    lenhei !== null
    && position === null
  ) {
    return showError(
      'growth-result',

      globalThis.ClinicalI18n
        ?.t?.(
          'growth.positionRequired'
        )
      || clinicalText(
        'Informe a posição da medida.',
        'Specify the measurement position.'
      )
    );
  }


  const payload = {
    sex,

    age_value:
      age,

    age_unit:
      ageUnit,

    age_basis:
      ageBasis,

    weight_kg:
      weight,

    length_height_cm:
      lenhei,

    measurement_position:
      position,

    head_circumference_cm:
      head,

    oedema
  };


  try {
    const {
      result,
      source
    } = await runClinicalCalculator(
      '/api/v1/tools/who-growth',
      payload,
      globalThis
        .ClinicalGrowthTools
        .calculateWhoGrowth
    );


    lastGrowthResult =
      result;

    lastGrowthSource =
      source;


    renderGrowthResult(
      result,
      source
    );

  } catch (error) {
    showError(
      'growth-result',
      error.message
    );
  }
}


function scoreGlasgow() {
  const ids = ['glasgow-e', 'glasgow-v', 'glasgow-m'];
  const values = ids.map((id) => document.getElementById(id).value);
  const total = document.getElementById('glasgow-total');
  const note = document.getElementById('glasgow-note');

  if (values.some((value) => value === '')) {
    total.textContent = '—';
    note.textContent = 'Selecione todos os componentes.';
    return;
  }

  const labels = ['E', 'V', 'M'];
  const components = values.map((value, index) => `${labels[index]}${value}`).join(' ');
  if (values.includes('NT')) {
    total.textContent = 'NT';
    note.textContent = `${components}. Quando um componente não é testável, registre os componentes e não reporte um total numérico.`;
    return;
  }

  const score = values.reduce((sum, value) => sum + Number.parseInt(value, 10), 0);
  total.textContent = String(score);
  note.textContent = components;
}

function scoreApgar() {
  const time = document.getElementById('apgar-time').value;
  const ids = ['apgar-a', 'apgar-p', 'apgar-g', 'apgar-t', 'apgar-r'];
  const values = ids.map((id) => document.getElementById(id).value);
  const total = document.getElementById('apgar-total');
  const note = document.getElementById('apgar-note');

  if (!time || values.some((value) => value === '')) {
    total.textContent = '—';
    note.textContent = 'Informe o momento e todos os cinco componentes.';
    return;
  }

  const score = values.reduce((sum, value) => sum + Number.parseInt(value, 10), 0);
  total.textContent = String(score);
  note.textContent = `Avaliação aos ${time} min. O Apgar descreve a condição do recém-nascido e não deve ser usado isoladamente para decidir o início da reanimação.`;
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(() => console.log('App Pronto para Instalação'))
      .catch((err) => console.log('Erro no SW', err));
  }
}

function wireUiEvents() {
  document.querySelectorAll('[data-tab]').forEach((button) => {
    button.addEventListener('click', () => switchTab(button.dataset.tab));
  });
  document.querySelectorAll('[data-policy]').forEach((button) => {
    button.addEventListener('click', () => loadPolicy(button.dataset.policy));
  });

  const submitHandlers = {
    'sae-search-form': searchSAE,
    'news2-form': calculateNews2,
    'renal-egfr-form': calculateEgfrTool,
    'renal-ckd-form': calculateCkdTool,
    'renal-aki-form': calculateAkiTool,
    'hemodynamics-form': calculateHemodynamicsTool,
    'oxygenation-form': calculateOxygenationTool,
    'metabolic-form': calculateMetabolicTool,
    'growth-form': calculateGrowthTool,
    'drip-form': calculateDrip,
    'meds-form': calculateMeds,
    'bmi-form': calculateBMI,
    'ped-form': calculatePed,
    'crcl-form': calculateCrCl,
    'naegele-form': calculateNaegele,
    'mcdonald-form': calculateMcDonald,
  };
  Object.entries(submitHandlers).forEach(([id, handler]) => {
    document.getElementById(id)?.addEventListener('submit', handler);
  });
  document.getElementById('glasgow-form')?.addEventListener('change', scoreGlasgow);
  document.getElementById('apgar-form')?.addEventListener('change', scoreApgar);

  const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
  tabs.forEach((tab, index) => {
    tab.addEventListener('keydown', (event) => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      let next = index;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      tabs[next].focus();
      switchTab(tabs[next].dataset.tab);
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  registerServiceWorker();
  wireUiEvents();
  checkApiHealth();
  if (typeof window !== 'undefined') {
    window.addEventListener('online', checkApiHealth);
    window.addEventListener('offline', checkApiHealth);
  }
});



globalThis.addEventListener?.(
  'clinical-language-change',
  () => {
    if (lastNews2Result) {
      renderNews2Result(
        lastNews2Result,
        lastNews2Source
      );
    }

    if (lastEgfrResult) {
      renderEgfrResult(
        lastEgfrResult,
        lastEgfrSource
      );
    }

    if (lastCkdResult) {
      renderCkdResult(
        lastCkdResult,
        lastCkdSource
      );
    }

    if (lastAkiResult) {
      renderAkiResult(
        lastAkiResult,
        lastAkiSource
      );
    }


    if (lastHemodynamicsResult) {
      renderHemodynamicsResult(
        lastHemodynamicsResult,
        lastHemodynamicsSource
      );
    }


    if (lastOxygenationResult) {
      renderOxygenationResult(
        lastOxygenationResult,
        lastOxygenationSource
      );
    }


    if (lastMetabolicResult) {
      renderMetabolicResult(
        lastMetabolicResult,
        lastMetabolicSource
      );
    }


    if (lastGrowthResult) {
      renderGrowthResult(
        lastGrowthResult,
        lastGrowthSource
      );
    }
  }
);
