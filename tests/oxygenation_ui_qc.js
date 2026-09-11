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


assert(
  html.includes(
    'id="oxygenation-form"'
  )
);

assert(
  html.includes(
    'id="oxygenation-result"'
  )
);

assert(
  html.includes(
    'data-i18n="oxygen.brazilSurveillance"'
  )
);

assert(
  html.includes(
    'data-i18n="oxygen.globalArdsStatus"'
  )
);


for (const key of [
  'oxygen.title',
  'oxygen.fio2',
  'oxygen.pao2',
  'oxygen.spo2',
  'oxygen.noArdsDiagnosis',
  'oxygen.brazilSurveillance',
  'oxygen.globalArdsStatus',
  'oxygen.offline'
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
    'clinical-reference-v22-v2-steadi-complementary'
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
    if (!elements.has(id)) {
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


// Force API-first calculation down the local/offline path.
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
  set(
    'oxygen-fio2',
    '40'
  );

  set(
    'oxygen-pao2',
    '80'
  );

  set(
    'oxygen-spo2',
    '95'
  );

  const result =
    set(
      'oxygenation-result'
    );


  await calculateOxygenationTool(
    event
  );


  assert(
    result.innerHTML
      .includes('200.0')
  );

  assert(
    result.innerHTML
      .includes('237.5')
  );

  assert(
    result.innerHTML
      .includes(
        'Resultado calculado localmente'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'não estabelecem diagnóstico'
      )
  );


  // Re-render the existing result in EN-GB.
  globalThis.ClinicalI18n = {
    getLanguage() {
      return 'en-GB';
    },

    t(key) {
      const messages = {
        'oxygen.result':
          'Calculated ratios',

        'oxygen.pf':
          'P/F ratio',

        'oxygen.sf':
          'S/F ratio',

        'oxygen.sfCaution':
          'S/F ratio interpretation caution',

        'oxygen.offline':
          'Result calculated locally while offline.',

        'oxygen.invalid':
          'Enter FiO₂ between 21% and 100% and at least one valid PaO₂ or SpO₂ value.'
      };

      return messages[key]
        || key;
    }
  };


  renderOxygenationResult(
    lastOxygenationResult,
    lastOxygenationSource
  );


  assert(
    result.innerHTML
      .includes(
        'P/F and S/F ratios quantify oxygenation'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'When used in the Global ARDS definition'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'Result calculated locally while offline.'
      )
  );


  // SpO2 >97% is still mathematically calculated,
  // but must display the explicit S/F caution.
  elements.get(
    'oxygen-pao2'
  ).value = '';

  elements.get(
    'oxygen-spo2'
  ).value = '98';


  await calculateOxygenationTool(
    event
  );


  assert(
    result.innerHTML
      .includes('245.0')
  );

  assert(
    result.innerHTML
      .includes(
        'SpO2 above 97%'
      )
  );

  assert(
    lastOxygenationResult
      .global_ards_sf_threshold_applicable
    === false
  );


  // PaO2-only path.
  elements.get(
    'oxygen-fio2'
  ).value = '50';

  elements.get(
    'oxygen-pao2'
  ).value = '75';

  elements.get(
    'oxygen-spo2'
  ).value = '';


  await calculateOxygenationTool(
    event
  );


  assert(
    result.innerHTML
      .includes('150.0')
  );

  assert.strictEqual(
    lastOxygenationResult.sf_ratio,
    null
  );


  // No PaO2 and no SpO2 must fail closed before calculation.
  elements.get(
    'oxygen-pao2'
  ).value = '';

  elements.get(
    'oxygen-spo2'
  ).value = '';


  await calculateOxygenationTool(
    event
  );


  assert(
    result.innerHTML
      .includes(
        'Enter FiO₂ between 21% and 100%'
      )
  );


  console.log(
    'oxygenation_ui_qc: bilingual API-first/offline P/F + S/F UI PASS'
  );

})().catch(
  error => {
    console.error(error);
    process.exit(1);
  }
);
