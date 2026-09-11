const fs = require('fs');
const vm = require('vm');
const assert = require('assert');


const html =
  fs.readFileSync(
    'index.html',
    'utf8'
  );


const toolsSource =
  fs.readFileSync(
    'assets/clinical-tools.js',
    'utf8'
  );


const appSource =
  fs.readFileSync(
    'assets/app.js',
    'utf8'
  );


const i18nSource =
  fs.readFileSync(
    'assets/i18n.js',
    'utf8'
  );


const swSource =
  fs.readFileSync(
    'sw.js',
    'utf8'
  );


for (const id of [
  'renal-egfr-form',
  'renal-ckd-form',
  'renal-aki-form',
  'renal-egfr-result',
  'renal-ckd-result',
  'renal-ckd-dialysis',
  'renal-aki-result'
]) {
  assert(
    html.includes(
      `id="${id}"`
    ),
    `missing ${id}`
  );
}


for (const key of [
  'renal.title',
  'renal.egfrTitle',
  'renal.ckdTitle',
  'renal.akiTitle',
  'renal.onDialysis',
  'renal.internationalTitle',
  'renal.brazilTitle',
  'renal.pcdtEquationBlocked',
  'renal.egfrBrazilAlignment',
  'renal.akiBrazilAlignment',
  'renal.offline'
]) {
  assert(
    i18nSource.includes(
      `'${key}'`
    ),
    `missing ${key}`
  );
}


assert(
  swSource.includes(
    'clinical-reference-v19-v2-brazil-oxygenation'
  )
);


const elements =
  new Map();


function makeElement(
  value = ''
) {
  return {
    value,
    checked: false,
    innerHTML: '',
    textContent: '',
    className: '',
    dataset: {},

    classList: {
      add() {},
      remove() {}
    },

    addEventListener() {},
    setAttribute() {},
    focus() {}
  };
}


function set(
  id,
  value = ''
) {
  const element =
    makeElement(value);

  elements.set(
    id,
    element
  );

  return element;
}


global.document = {
  getElementById(id) {
    if (
      !elements.has(id)
    ) {
      elements.set(
        id,
        makeElement()
      );
    }

    return elements.get(id);
  },

  querySelectorAll() {
    return [];
  },

  addEventListener() {}
};


global.navigator = {};
global.URL = URL;


// Force API-first calculations down the local/offline path.
global.fetch = async () => {
  throw new TypeError(
    'Failed to fetch'
  );
};


vm.runInThisContext(
  toolsSource,
  {
    filename:
      'assets/clinical-tools.js'
  }
);


vm.runInThisContext(
  appSource,
  {
    filename:
      'assets/app.js'
  }
);


const event = {
  preventDefault() {}
};


(async () => {
  // eGFR offline UI
  set(
    'renal-egfr-age',
    '18'
  );

  set(
    'renal-egfr-sex',
    'male'
  );

  set(
    'renal-egfr-cr',
    '0.9'
  );

  set(
    'renal-egfr-unit',
    'mg/dL'
  );

  set(
    'renal-ckd-egfr',
    ''
  );

  const egfrResult =
    set(
      'renal-egfr-result'
    );


  await calculateEgfrTool(
    event
  );


  assert(
    egfrResult.innerHTML
      .includes('127.0')
  );

  assert(
    egfrResult.innerHTML
      .includes(
        'Resultado calculado localmente'
      )
  );

  assert.strictEqual(
    elements.get(
      'renal-ckd-egfr'
    ).value,
    '127.0'
  );


  // CKD G/A offline UI
  elements.get(
    'renal-ckd-egfr'
  ).value = '40';

  set(
    'renal-ckd-acr',
    '100'
  );

  set(
    'renal-ckd-acr-unit',
    'mg/g'
  );

  const chronicity =
    set(
      'renal-ckd-chronicity'
    );

  chronicity.checked = true;

  const marker =
    set(
      'renal-ckd-other-marker'
    );

  marker.checked = false;

  const dialysis =
    set(
      'renal-ckd-dialysis'
    );

  dialysis.checked = false;

  const ckdResult =
    set(
      'renal-ckd-result'
    );


  await calculateCkdTool(
    event
  );


  assert(
    ckdResult.innerHTML
      .includes('G3b/A2')
  );

  assert(
    ckdResult.innerHTML
      .includes(
        'atendem à definição de DRC'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        'Brasil · SUS PCDT'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        'Estágio 3B'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        'não é executada'
      )
  );


  // Exact 300 mg/g PCDT ambiguity + dialysis 5D context.
  elements.get(
    'renal-ckd-egfr'
  ).value = '14.9';

  elements.get(
    'renal-ckd-acr'
  ).value = '300';

  dialysis.checked = true;


  await calculateCkdTool(
    event
  );


  assert(
    ckdResult.innerHTML
      .includes(
        'Estágio 5D'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        '300 mg/g'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        'textualmente sem categoria'
      )
  );


  // Urine-output-only AKI offline UI.
  set(
    'renal-aki-current',
    ''
  );

  set(
    'renal-aki-current-unit',
    'mg/dL'
  );

  set(
    'renal-aki-baseline',
    ''
  );

  set(
    'renal-aki-baseline-unit',
    'mg/dL'
  );

  set(
    'renal-aki-interval',
    ''
  );

  set(
    'renal-aki-weight',
    '70'
  );

  set(
    'renal-aki-urine',
    '200'
  );

  set(
    'renal-aki-urine-hours',
    '6'
  );

  set(
    'renal-aki-anuria',
    ''
  );

  const krt =
    set(
      'renal-aki-krt'
    );

  krt.checked = false;

  const akiResult =
    set(
      'renal-aki-result'
    );


  await calculateAkiTool(
    event
  );


  assert(
    akiResult.innerHTML
      .includes(
        'KDIGO estágio 1'
      )
  );

  assert(
    akiResult.innerHTML
      .includes(
        '0.4762'
      )
  );


  // Existing calculated results must be capable of English rendering
  // without recalculation.
  globalThis.ClinicalI18n = {
    getLanguage() {
      return 'en-GB';
    },

    t(key) {
      return key;
    }
  };


  renderEgfrResult(
    lastEgfrResult,
    lastEgfrSource
  );

  renderCkdResult(
    lastCkdResult,
    lastCkdSource
  );

  renderAkiResult(
    lastAkiResult,
    lastAkiSource
  );


  assert(
    egfrResult.innerHTML
      .includes(
        'Estimated GFR indexed'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        'meet the CKD definition'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        'Stage 5D'
      )
  );

  assert(
    ckdResult.innerHTML
      .includes(
        '300 mg/g'
      )
  );

  assert(
    akiResult.innerHTML
      .includes(
        'KDIGO stage 1'
      )
  );


  console.log(
    'renal_ui_qc: bilingual API-first/offline renal UI PASS'
  );

})().catch(
  error => {
    console.error(error);
    process.exit(1);
  }
);
