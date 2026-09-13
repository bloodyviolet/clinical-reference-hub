const fs =
  require('fs');

const vm =
  require('vm');

const assert =
  require('assert');


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


const elements =
  new Map();


function makeElement(
  value = ''
) {
  return {
    value,
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
    makeElement(
      value
    );

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
global.caches = undefined;


let language =
  'pt-BR';


const messages = {
  'pt-BR': {
    'neuro.offline':
      'Resultado calculado localmente em modo offline a partir do espelho qualificado do núcleo clínico.',

    'neuro.gcs.result':
      'Resultado · Glasgow',

    'neuro.gcs.incomplete':
      'Há componente não testável: preserve os componentes individuais e não reporte total numérico.',

    'neuro.gcsp.result':
      'Resultado · GCS-P',

    'neuro.gcsp.incomplete':
      'GCS-P sem resultado numérico: é necessário GCS numérico e reatividade pupilar conhecida.',

    'neuro.gcsp.noPrognosis':
      'Nenhuma probabilidade prognóstica é inferida por esta ferramenta.',

    'neuro.four.result':
      'Resultado · FOUR Score',

    'neuro.four.incomplete':
      'Um ou mais domínios estão indisponíveis; não reporte total numérico.',

    'neuro.four.noCutoff':
      'Nenhum limiar de mortalidade, tratamento ou disposição é inferido.'
  },

  'en-GB': {
    'neuro.offline':
      'Result calculated locally while offline using the qualified mirror of the clinical core.',

    'neuro.gcs.result':
      'Result · Glasgow',

    'neuro.gcs.incomplete':
      'A component is not testable: preserve the individual components and do not report a numeric total.',

    'neuro.gcsp.result':
      'Result · GCS-P',

    'neuro.gcsp.incomplete':
      'No numeric GCS-P result: a numeric GCS and known pupil reactivity are required.',

    'neuro.gcsp.noPrognosis':
      'This tool does not infer prognostic probabilities.',

    'neuro.four.result':
      'Result · FOUR Score',

    'neuro.four.incomplete':
      'One or more domains are unavailable; do not report a numeric total.',

    'neuro.four.noCutoff':
      'No mortality, treatment or disposition threshold is inferred.'
  }
};


globalThis.ClinicalI18n = {
  getLanguage() {
    return language;
  },

  t(key) {
    return (
      messages[language][key]
      || key
    );
  }
};


vm.runInThisContext(
  toolsSource,
  {
    filename:
      'assets/clinical-tools.js'
  }
);


let mode =
  'api';

const calls =
  [];


global.fetch =
  async (
    url,
    options
  ) => {
    calls.push(
      url
    );

    if (mode === 'offline') {
      throw new TypeError(
        'Failed to fetch'
      );
    }

    const payload =
      JSON.parse(
        options.body
      );

    let result;

    if (
      url
      === '/api/v1/tools/gcs'
    ) {
      result =
        ClinicalTools
          .calculateGcs(
            payload
          );

    } else if (
      url
      === '/api/v1/tools/gcs-p'
    ) {
      result =
        ClinicalTools
          .calculateGcsp(
            payload
          );

    } else if (
      url
      === '/api/v1/tools/four-score'
    ) {
      result =
        ClinicalTools
          .calculateFour(
            payload
          );

    } else {
      throw new Error(
        `unexpected URL ${url}`
      );
    }

    return {
      ok:
        true,

      status:
        200,

      async json() {
        return result;
      }
    };
  };


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
  // Online GCS.
  set(
    'glasgow-e',
    '4'
  );

  set(
    'glasgow-v',
    '5'
  );

  set(
    'glasgow-m',
    '6'
  );

  const gcsResult =
    set(
      'glasgow-result'
    );

  await calculateGcsTool(
    event
  );

  assert(
    calls.includes(
      '/api/v1/tools/gcs'
    )
  );

  assert(
    gcsResult.innerHTML
      .includes('15')
  );

  assert(
    gcsResult.innerHTML
      .includes('E4 V5 M6')
  );


  // Offline GCS with NT: no fake numeric total.
  mode =
    'offline';

  elements.get(
    'glasgow-v'
  ).value =
    'NT';

  await calculateGcsTool(
    event
  );

  assert(
    gcsResult.innerHTML
      .includes('NT')
  );

  assert(
    gcsResult.innerHTML
      .includes(
        'Resultado calculado localmente'
      )
  );


  // Offline GCS-P with unknown pupil state.
  set(
    'gcsp-e',
    '4'
  );

  set(
    'gcsp-v',
    '5'
  );

  set(
    'gcsp-m',
    '6'
  );

  set(
    'gcsp-pupils',
    'UNKNOWN'
  );

  const gcspResult =
    set(
      'gcsp-result'
    );

  await calculateGcspTool(
    event
  );

  assert(
    calls.includes(
      '/api/v1/tools/gcs-p'
    )
  );

  assert(
    gcspResult.innerHTML
      .includes('GCS-P')
  );

  assert(
    gcspResult.innerHTML
      .includes('PRS')
  );

  assert(
    gcspResult.innerHTML
      .includes(
        'Nenhuma probabilidade prognóstica'
      )
  );


  // Offline FOUR with an explicitly unavailable domain.
  set(
    'four-eye',
    '4'
  );

  set(
    'four-motor',
    '4'
  );

  set(
    'four-brainstem',
    'UNAVAILABLE'
  );

  set(
    'four-respiration',
    '4'
  );

  const fourResult =
    set(
      'four-result'
    );

  await calculateFourTool(
    event
  );

  assert(
    calls.includes(
      '/api/v1/tools/four-score'
    )
  );

  assert(
    fourResult.innerHTML
      .includes(
        'Um ou mais domínios'
      )
  );

  assert(
    !fourResult.innerHTML
      .includes('>16<')
  );


  // Existing result can be re-rendered in EN-GB.
  language =
    'en-GB';

  renderFourResult(
    lastFourResult,
    lastFourSource
  );

  assert(
    fourResult.innerHTML
      .includes(
        'One or more domains are unavailable'
      )
  );

  assert(
    fourResult.innerHTML
      .includes(
        'Result calculated locally while offline'
      )
  );


  assert(
    !appSource.includes(
      'function scoreGlasgow()'
    )
  );

  assert(
    !appSource.includes(
      "addEventListener('change', scoreGlasgow)"
    )
  );


  console.log(
    'four_gcsp_ui_qc: '
    + 'API-first + qualified offline GCS/GCS-P/FOUR UI PASS'
  );
})();
