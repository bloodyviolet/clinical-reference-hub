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
    'id="metabolic-form"'
  )
);

assert(
  html.includes(
    'id="metabolic-result"'
  )
);

assert(
  html.includes(
    'id="metabolic-acidosis-confirmed"'
  )
);


for (const key of [
  'metabolic.title',
  'metabolic.sodium',
  'metabolic.confirmed',
  'metabolic.gateWarning',
  'metabolic.winter',
  'metabolic.delta',
  'metabolic.offline'
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


// Force API-first calculations to the local/offline engine.
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
    'metabolic-na',
    '140'
  );

  set(
    'metabolic-cl',
    '104'
  );

  set(
    'metabolic-hco3',
    '16'
  );

  set(
    'metabolic-albumin',
    '4'
  );

  set(
    'metabolic-glucose',
    '500'
  );

  set(
    'metabolic-bun',
    '28'
  );

  set(
    'metabolic-paco2',
    '32'
  );

  const confirmed =
    set(
      'metabolic-acidosis-confirmed'
    );

  confirmed.checked = true;

  const result =
    set(
      'metabolic-result'
    );


  await calculateMetabolicTool(
    event
  );


  assert(
    result.innerHTML
      .includes('20.0 mEq/L')
  );

  assert(
    result.innerHTML
      .includes('317.8 mOsm/kg')
  );

  assert(
    result.innerHTML
      .includes('146.4 mEq/L')
  );

  assert(
    result.innerHTML
      .includes('32.0')
  );

  assert(
    result.innerHTML
      .includes('30.0–34.0')
  );

  assert(
    result.innerHTML
      .includes('1.00')
  );

  assert(
    result.innerHTML
      .includes(
        'Resultado calculado localmente'
      )
  );


  assert.strictEqual(
    lastMetabolicResult
      .winter_analysis_applied,
    true
  );

  assert.strictEqual(
    lastMetabolicResult
      .delta_analysis_applied,
    true
  );


  // Existing result must re-render in EN-GB without recalculation.
  globalThis.ClinicalI18n = {
    getLanguage() {
      return 'en-GB';
    },

    t(key) {
      const messages = {
        'metabolic.result':
          'Calculated results',

        'metabolic.ag':
          'Anion gap',

        'metabolic.correctedAg':
          'Albumin-corrected anion gap',

        'metabolic.osmolality':
          'Calculated osmolality',

        'metabolic.correctedNa':
          'Corrected sodium',

        'metabolic.winter':
          'Winter compensation',

        'metabolic.delta':
          'Delta ratio',

        'metabolic.validity':
          'Validity / limitations',

        'metabolic.offline':
          'Result calculated locally while offline.',

        'metabolic.invalid':
          'Enter valid metabolic values.',

        'metabolic.agPair':
          'Chloride and bicarbonate must be supplied together.'
      };

      return messages[key]
        || key;
    }
  };


  renderMetabolicResult(
    lastMetabolicResult,
    lastMetabolicSource
  );


  assert(
    result.innerHTML
      .includes(
        'Mathematical results supporting metabolic/acid-base assessment'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'PaCO2 is within the Winter expected range'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'compatible with predominant high-anion-gap metabolic acidosis'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'Result calculated locally while offline.'
      )
  );


  // Turn off the explicit metabolic-acidosis gate.
  confirmed.checked = false;


  await calculateMetabolicTool(
    event
  );


  assert.strictEqual(
    lastMetabolicResult
      .winter_analysis_applied,
    false
  );

  assert.strictEqual(
    lastMetabolicResult
      .delta_analysis_applied,
    false
  );

  assert(
    result.innerHTML
      .includes(
        'not explicitly confirmed'
      )
  );


  // Partial AG chemistry must fail closed at UI level.
  elements.get(
    'metabolic-hco3'
  ).value = '';


  await calculateMetabolicTool(
    event
  );


  assert(
    result.innerHTML
      .includes(
        'Chloride and bicarbonate must be supplied together.'
      )
  );


  console.log(
    'metabolic_ui_qc: bilingual API-first/offline metabolic UI PASS'
  );

})().catch(
  error => {
    console.error(error);
    process.exit(1);
  }
);
