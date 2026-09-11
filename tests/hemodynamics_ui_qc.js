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
    'id="hemodynamics-form"'
  )
);

assert(
  html.includes(
    'id="hemodynamics-result"'
  )
);

assert(
  html.includes(
    'id="hemo-context"'
  )
);

assert(
  html.includes(
    'value="septic_shock"'
  )
);

assert(
  html.includes(
    'value="obstetric_hemorrhage"'
  )
);


for (const key of [
  'hemo.title',
  'hemo.sbp',
  'hemo.dbp',
  'hemo.hr',
  'hemo.context',
  'hemo.contextNone',
  'hemo.contextSeptic',
  'hemo.contextObstetric',
  'hemo.contextHelp',
  'hemo.contextResult',
  'hemo.brazilSource',
  'hemo.noThreshold',
  'hemo.offline'
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
    'clinical-reference-v20-v2-brazil-methanol'
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


// Simulate loss of network so the UI must fall back to
// the local ClinicalTools implementation.
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
    'hemo-sbp',
    '120'
  );

  set(
    'hemo-dbp',
    '80'
  );

  set(
    'hemo-hr',
    '60'
  );

  const clinicalContext =
    set(
      'hemo-context',
      'none'
    );

  const result =
    set(
      'hemodynamics-result'
    );


  await calculateHemodynamicsTool(
    event
  );


  assert(
    result.innerHTML
      .includes('40.0 mmHg')
  );

  assert(
    result.innerHTML
      .includes('93.3 mmHg')
  );

  assert(
    result.innerHTML
      .includes('0.500')
  );

  assert(
    result.innerHTML
      .includes('0.643')
  );

  assert(
    result.innerHTML
      .includes(
        'Resultado calculado localmente'
      )
  );

  assert(
    !result.innerHTML
      .includes(
        'Contexto brasileiro —'
      )
  );


  // Context must be explicitly selected.
  elements.get(
    'hemo-sbp'
  ).value = '85';

  elements.get(
    'hemo-dbp'
  ).value = '55';

  elements.get(
    'hemo-hr'
  ).value = '90';

  clinicalContext.value =
    'septic_shock';


  await calculateHemodynamicsTool(
    event
  );


  assert(
    result.innerHTML
      .includes(
        'Contexto brasileiro — choque séptico'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'em ou acima de 65 mmHg'
      )
  );


  // Ministry obstetric source uses strict >0.9.
  elements.get(
    'hemo-sbp'
  ).value = '100';

  elements.get(
    'hemo-dbp'
  ).value = '70';

  elements.get(
    'hemo-hr'
  ).value = '90';

  clinicalContext.value =
    'obstetric_hemorrhage';


  await calculateHemodynamicsTool(
    event
  );


  assert(
    result.innerHTML
      .includes(
        '0.900'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'não está acima de 0,9'
      )
  );


  elements.get(
    'hemo-hr'
  ).value = '91';


  await calculateHemodynamicsTool(
    event
  );


  assert(
    result.innerHTML
      .includes(
        '0.910'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'está acima de 0,9'
      )
  );


  // Language switch must re-render an existing result,
  // not require a new calculation.
  globalThis.ClinicalI18n = {
    getLanguage() {
      return 'en-GB';
    },

    t(key) {
      const messages = {
        'hemo.result':
          'Calculated indices',

        'hemo.pp':
          'Pulse pressure',

        'hemo.map':
          'Mean arterial pressure',

        'hemo.contextResult':
          'Contextual Brazilian guidance',

        'hemo.offline':
          'Result calculated locally while offline.'
      };

      return messages[key]
        || key;
    }
  };


  renderHemodynamicsResult(
    lastHemodynamicsResult,
    lastHemodynamicsSource
  );


  assert(
    result.innerHTML
      .includes(
        'These indices are adjuncts'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'Brazilian context — obstetric haemorrhage'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'Shock Index is above 0.9'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'Contextual Brazilian guidance'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'Calculated MAP is an approximation'
      )
  );

  assert(
    result.innerHTML
      .includes(
        'Result calculated locally while offline.'
      )
  );


  // Reversed SBP/DBP must fail before calculation.
  elements.get(
    'hemo-sbp'
  ).value = '70';

  elements.get(
    'hemo-dbp'
  ).value = '80';


  await calculateHemodynamicsTool(
    event
  );


  assert(
    result.innerHTML
      .includes(
        'hemo.invalid'
      )
    || result.innerHTML
      .includes(
        'Enter valid'
      )
  );


  console.log(
    'hemodynamics_ui_qc: bilingual API-first/offline UI PASS'
  );

})().catch(
  error => {
    console.error(error);
    process.exit(1);
  }
);
