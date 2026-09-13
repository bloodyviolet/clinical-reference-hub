const fs =
  require('fs');

const assert =
  require('assert');


const html =
  fs.readFileSync(
    'index.html',
    'utf8'
  );

const app =
  fs.readFileSync(
    'assets/app.js',
    'utf8'
  );

const tools =
  fs.readFileSync(
    'assets/clinical-tools.js',
    'utf8'
  );

const i18n =
  fs.readFileSync(
    'assets/i18n.js',
    'utf8'
  );

const sw =
  fs.readFileSync(
    'sw.js',
    'utf8'
  );


for (const id of [
  'glasgow-form',
  'glasgow-e',
  'glasgow-v',
  'glasgow-m',
  'glasgow-result',
  'gcsp-form',
  'gcsp-e',
  'gcsp-v',
  'gcsp-m',
  'gcsp-pupils',
  'gcsp-result',
  'four-form',
  'four-eye',
  'four-motor',
  'four-brainstem',
  'four-respiration',
  'four-result'
]) {
  assert(
    html.includes(
      `id="${id}"`
    ),
    `missing ${id}`
  );
}


for (const key of [
  'neuro.gcs.title',
  'neuro.gcs.nt',
  'neuro.gcsp.title',
  'neuro.gcsp.pupilUnknown',
  'neuro.four.title',
  'neuro.four.brainstem',
  'neuro.four.respiration',
  'neuro.four.source',
  'neuro.offline'
]) {
  assert(
    i18n.includes(
      `'${key}'`
    ),
    `missing ${key}`
  );

  assert(
    html.includes(
      `data-i18n="${key}"`
    )
    || key === 'neuro.offline',
    `missing DOM i18n use ${key}`
  );
}


for (const symbol of [
  'calculateGcs',
  'calculateGcsp',
  'calculateFour'
]) {
  assert(
    tools.includes(
      symbol
    )
  );
}


for (const token of [
  'function calculateGcsTool(',
  'function calculateGcspTool(',
  'function calculateFourTool(',
  "'/api/v1/tools/gcs'",
  "'/api/v1/tools/gcs-p'",
  "'/api/v1/tools/four-score'",
  "'glasgow-form': calculateGcsTool",
  "'gcsp-form': calculateGcspTool",
  "'four-form': calculateFourTool"
]) {
  assert(
    app.includes(
      token
    ),
    `missing ${token}`
  );
}


assert(
  !app.includes(
    'function scoreGlasgow()'
  )
);

assert(
  !app.includes(
    "addEventListener('change', scoreGlasgow)"
  )
);

assert(
  !html.includes(
    'id="glasgow-total"'
  )
);

assert(
  !html.includes(
    'id="glasgow-note"'
  )
);


// There is no direct-total GCS-P input.
assert(
  !html.includes(
    'id="gcsp-total"'
  )
);

assert(
  !html.includes(
    'id="gcsp-gcs-result"'
  )
);


assert(
  sw.includes(
    'clinical-reference-v24-v2-serial-trends-ui'
  )
);

const previousItem10Cache =
  [
    'clinical-reference-v22',
    'v2-steadi-complementary'
  ].join('-');


assert(
  !sw.includes(
    previousItem10Cache
  )
);


console.log(
  'four_gcsp_ui_static_qc: '
  + 'DOM + API authority + bilingual keys + current cache PASS'
);
