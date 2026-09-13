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

assert(
  html.includes(
    'id="methanol-form"'
  )
);

assert(
  html.includes(
    'id="methanol-context-confirmed"'
  )
);

assert(
  html.includes(
    'id="methanol-result"'
  )
);

assert(
  html.includes(
    'id="methanol-urea"'
  )
);

assert(
  html.includes(
    'id="methanol-measured-osm"'
  )
);


for (const key of [
  'metabolic.title',
  'metabolic.sodium',
  'metabolic.confirmed',
  'metabolic.gateWarning',
  'metabolic.winter',
  'metabolic.delta',
  'metabolic.offline',
  'methanol.title',
  'methanol.explicit',
  'methanol.glucose',
  'methanol.urea',
  'methanol.measuredOsm',
  'methanol.noDiagnosis',
  'methanol.unitWarning',
  'methanol.offline'
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
    'clinical-reference-v24-v2-serial-trends-ui'
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
          'Chloride and bicarbonate must be supplied together.',

        'methanol.result':
          'Results · Brazilian methanol context',

        'methanol.ministryAg':
          'Ministry-workflow anion gap',

        'methanol.calculatedOsm':
          'Ministry-workflow calculated osmolality',

        'methanol.osmolarGap':
          'Osmolar gap',

        'methanol.thresholds':
          'Contextual workflow thresholds',

        'methanol.yes':
          'Yes',

        'methanol.no':
          'No',

        'methanol.validity':
          'Safety / limitations',

        'methanol.noDiagnosis':
          'These results do not independently diagnose methanol poisoning.',

        'methanol.unitWarning':
          'Do not reuse mg/dL glucose or BUN from the general toolkit: this context requires glucose and urea explicitly in mmol/L.',

        'methanol.contextRequired':
          'Explicitly confirm the clinical context of suspected methanol poisoning.',

        'methanol.offline':
          'Toxicology result calculated locally while offline.'
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


  // Separate Ministry methanol UI must remain explicitly gated.
  const methanolContext =
    set(
      'methanol-context-confirmed'
    );

  methanolContext.checked = true;

  set(
    'methanol-na',
    '140'
  );

  set(
    'methanol-k',
    '4'
  );

  set(
    'methanol-cl',
    '104'
  );

  set(
    'methanol-hco3',
    '20'
  );

  set(
    'methanol-glucose',
    '5'
  );

  set(
    'methanol-urea',
    '5'
  );

  set(
    'methanol-measured-osm',
    '305'
  );

  const methanolResult =
    set(
      'methanol-result'
    );


  await calculateBrazilMethanolTool(
    event
  );


  assert.strictEqual(
    lastMethanolResult
      .ministry_anion_gap_mmol_l,
    20
  );

  assert.strictEqual(
    lastMethanolResult
      .ministry_osmolality_uses_urea_not_bun,
    true
  );

  assert.strictEqual(
    lastMethanolResult
      .methanol_diagnosis_applied,
    false
  );

  assert.strictEqual(
    lastMethanolResult
      .automatic_toxicology_context_inference_applied,
    false
  );

  assert(
    methanolResult.innerHTML
      .includes(
        '20.00 mmol/L'
      )
  );

  assert(
    methanolResult.innerHTML
      .includes(
        '290.75 mOsm/kg'
      )
  );

  assert(
    methanolResult.innerHTML
      .includes(
        '14.25 mOsm/kg'
      )
  );

  assert(
    methanolResult.innerHTML
      .includes(
        'urea is not BUN'
      )
  );

  assert(
    methanolResult.innerHTML
      .includes(
        'do not independently diagnose methanol poisoning'
      )
  );

  assert(
    methanolResult.innerHTML
      .includes(
        'Toxicology result calculated locally while offline.'
      )
  );


  methanolContext.checked = false;


  await calculateBrazilMethanolTool(
    event
  );


  assert(
    methanolResult.innerHTML
      .includes(
        'Explicitly confirm the clinical context of suspected methanol poisoning.'
      )
  );


  console.log(
    'metabolic_ui_qc: bilingual API-first/offline metabolic + methanol UI PASS'
  );

})().catch(
  error => {
    console.error(error);
    process.exit(1);
  }
);
