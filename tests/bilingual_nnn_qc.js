#!/usr/bin/env node

const fs = require('fs');
const assert = require('assert');

const app = fs.readFileSync(
  'assets/app.js',
  'utf8'
);

const sw = fs.readFileSync(
  'sw.js',
  'utf8'
);

const sae = JSON.parse(
  fs.readFileSync(
    'assets/offline/sae.json',
    'utf8'
  )
);

assert.strictEqual(
  sae.api_version,
  '1.4.5'
);

assert.strictEqual(
  sae.database_revision,
  '0007'
);

assert.strictEqual(
  sae.count,
  277
);

for (const item of sae.items) {
  for (const field of [
    'description_pt',
    'description_en',
    'nic_label_pt',
    'nic_label_en',
    'noc_label_pt',
    'noc_label_en',
    'intervention_pt',
    'intervention_en',
    'outcome_pt',
    'outcome_en',
  ]) {
    assert(
      item[field] &&
      String(item[field]).trim(),
      `${item.code}: missing ${field}`
    );
  }
}

for (const token of [
  'item.intervention_pt',
  'item.intervention_en',
  'item.outcome_pt',
  'item.outcome_en',
  'lang="pt-BR"',
  'lang="en-GB"',
  'PT-BR:',
  'EN-GB:',
]) {
  assert(
    app.includes(token),
    `assets/app.js missing ${token}`
  );
}

assert(
  sw.includes(
    'clinical-reference-v12-v2-oxygenation'
  ),
  'service-worker cache version not bumped'
);

console.log(
  'bilingual_nnn_qc: ' +
  '277 SAE records complete; ' +
  'PT-BR + EN-GB NIC/NOC rendering PASS'
);
