const fs =
  require('fs');

const vm =
  require('vm');

const crypto =
  require('crypto');

const assert =
  require('assert');


const app =
  fs.readFileSync(
    'assets/app.js',
    'utf8'
  );

const html =
  fs.readFileSync(
    'index.html',
    'utf8'
  );

const presentation =
  fs.readFileSync(
    'assets/bilingual-presentation.js',
    'utf8'
  );

const policyTranslations =
  fs.readFileSync(
    'assets/policy-translations-en.js',
    'utf8'
  );

const policyBundle =
  JSON.parse(
    fs.readFileSync(
      'assets/offline/policies.json',
      'utf8'
    )
  );

const sw =
  fs.readFileSync(
    'sw.js',
    'utf8'
  );

const main =
  fs.readFileSync(
    'main.py',
    'utf8'
  );

const preflight =
  fs.readFileSync(
    'scripts/preflight.py',
    'utf8'
  );


function sha256(
  value
) {
  return crypto
    .createHash(
      'sha256'
    )
    .update(
      value
    )
    .digest(
      'hex'
    );
}


function block(
  startToken,
  endToken
) {
  const start =
    app.indexOf(
      startToken
    );

  const end =
    app.indexOf(
      endToken,
      start
    );

  assert(
    start >= 0,
    startToken
  );

  assert(
    end > start,
    endToken
  );

  return app.slice(
    start,
    end
  );
}


assert.strictEqual(
  sha256(
    block(
      'function renderContextualLinks(',
      'function isPositiveFinite('
    )
  ),
  'ab49dcd551546e71c0a7cd6cb06aa9cd626e2f54604077c7a949fad277884988'
);


assert.strictEqual(
  sha256(
    block(
      'async function searchSAE(',
      'async function loadPolicy('
    )
  ),
  '00e92220418e173e78b0e1609a2e48300efddbdea7a2ef6c9ecfa09f4fbd89b9'
);


vm.runInThisContext(
  policyTranslations,
  {
    filename:
      'assets/policy-translations-en.js'
  }
);


const translator =
  globalThis
    .ClinicalPolicyTranslations;


assert(translator);

assert.strictEqual(
  translator.count,
  54
);


const rows = [];

for (
  const [
    policyName,
    payload
  ]
  of Object.entries(
    policyBundle.policies
  )
) {
  for (
    const item
    of payload.items
  ) {
    rows.push(
      {
        policyName,
        item
      }
    );
  }
}


assert.strictEqual(
  rows.length,
  54
);


for (
  const {
    policyName,
    item
  }
  of rows
) {
  assert.strictEqual(
    item.policy_name,
    policyName
  );

  const translated =
    translator.translateItem(
      item,
      'en-GB'
    );

  assert(translated);
  assert.strictEqual(
    translated.id,
    item.id
  );

  assert.strictEqual(
    translated.source_url,
    item.source_url
  );

  assert.notStrictEqual(
    translated.directive,
    item.directive
  );

  assert.notStrictEqual(
    translated.target_demographic,
    item.target_demographic
  );

  assert.notStrictEqual(
    translated.clinical_guideline,
    item.clinical_guideline
  );
}


for (
  const token
  of [
    '#sae-input',
    '#view-policy h2',
    'drip-form',
    'meds-form',
    'bmi-form',
    'ped-form',
    'crcl-form',
    'naegele-form',
    'mcdonald-form',
    'apgar-form',
    'Search NANDA Diagnosis',
    'Public Health Policies and Guidance',
    'Calculate Volume to Draw Up',
    'Apgar Score'
  ]
) {
  assert(
    presentation.includes(
      token
    ),
    token
  );
}


for (
  const forbidden
  of [
    'fetch(',
    'XMLHttpRequest',
    'localStorage',
    'sessionStorage',
    'indexedDB',
    'WebSocket'
  ]
) {
  assert(
    !presentation.includes(
      forbidden
    ),
    forbidden
  );
}


for (
  const token
  of [
    'ClinicalPolicyTranslations',
    'clinicalText(',
    'activePolicy',
    'legacyRerenders',
    'scoreApgar();',
    'toLocaleDateString('
  ]
) {
  assert(
    app.includes(
      token
    ),
    token
  );
}


/*
 * Clinical arithmetic invariants:
 * translation work must not alter formulae.
 */

for (
  const formula
  of [
    'const gotas =',
    '(v * DRIP_FACTORS.macro) / minutes',
    'const micro =',
    '(v * DRIP_FACTORS.micro) / minutes',
    'const result =',
    '(prescribedBase * vol) / availableBase',
    'const bmi =',
    'w / (h * h)',
    'w * 100',
    '1000',
    '((w - 10) * 50)',
    '1500',
    '((w - 20) * 20)',
    '((140 - age) * w) / (72 * cr)',
    'crcl *= 0.85',
    '+ 280',
    '((au * 8) / 7) * 7',
    'sum',
    'Number.parseInt('
  ]
) {
  assert(
    app.includes(
      formula
    ),
    formula
  );
}


assert(
  html.includes(
    '/manifest.json?v=28'
  )
);

assert(
  html.includes(
    '/assets/policy-translations-en.js'
  )
);

assert(
  html.includes(
    '/assets/bilingual-presentation.js'
  )
);


assert(
  sw.includes(
    'clinical-reference-v28-v2-bilingual-completeness'
  )
);

assert(
  sw.includes(
    "'/manifest.json?v=28'"
  )
);

assert(
  sw.includes(
    "'/assets/policy-translations-en.js'"
  )
);

assert(
  sw.includes(
    "'/assets/bilingual-presentation.js'"
  )
);


for (
  const source
  of [
    main,
    preflight
  ]
) {
  assert(
    source.includes(
      'policy-translations-en.js'
    )
  );

  assert(
    source.includes(
      'bilingual-presentation.js'
    )
  );
}


console.log(
  'bilingual_presentation_qc: NNN hard-freeze, 54 policy translations, static bilingual presentation, legacy result rerender and formula invariants PASS'
);
