const fs = require('fs');
const vm = require('vm');
const assert = require('assert');


const html =
  fs.readFileSync(
    'index.html',
    'utf8'
  );


const growthSource =
  fs.readFileSync(
    'assets/growth-tools.js',
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
    'id="growth-form"'
  )
);

assert(
  html.includes(
    'id="growth-result"'
  )
);

assert(
  html.includes(
    'id="growth-age-basis"'
  )
);

assert(
  html.includes(
    'id="growth-oedema"'
  )
);


for (const key of [
  'growth.title',
  'growth.correctedNote',
  'growth.who',
  'growth.brazil',
  'growth.noEndorsement',
  'growth.offline'
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


assert(
  swSource.includes(
    '/assets/reference/who-growth/NOTICE.txt'
  )
);


assert(
  swSource.includes(
    '/assets/reference/who-growth/GPL-3.0.txt'
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
global.caches = undefined;


globalThis.ClinicalI18n = {
  getLanguage() {
    return 'pt-BR';
  },

  t(key) {
    const messages = {
      'growth.results':
        'Resultados de crescimento',

      'growth.wfa':
        'Peso para idade',

      'growth.hfa':
        'Comprimento / estatura para idade',

      'growth.wflh':
        'Peso para comprimento / estatura',

      'growth.bfa':
        'IMC para idade',

      'growth.hcfa':
        'Perímetro cefálico para idade',

      'growth.z':
        'Escore-z',

      'growth.percentile':
        'Percentil',

      'growth.percentileUnavailable':
        'Indisponível fora de ±3 DP',

      'growth.who':
        'WHO',

      'growth.brazil':
        'Brasil · SISVAN',

      'growth.noNamedClass':
        'Sem classificação nominal adicional',

      'growth.warning':
        'Observações / alertas',

      'growth.adjustment':
        'Ajuste de posição aplicado',

      'growth.bmi':
        'IMC calculado',

      'growth.offline':
        'Resultado calculado localmente com as tabelas WHO precacheadas.',

      'growth.invalid':
        'Informe sexo, idade válida e pelo menos uma medida antropométrica.',

      'growth.positionRequired':
        'Informe se a medida foi obtida como comprimento recumbente ou estatura em pé.'
    };

    return messages[key]
      || key;
  }
};


global.fetch =
  async function growthUiFetch(
    url
  ) {
    const value =
      String(url);


    if (
      value.startsWith(
        '/api/v1/'
      )
    ) {
      throw new TypeError(
        'Failed to fetch'
      );
    }


    const localPath =
      value.replace(
        /^\/+/,
        ''
      );


    const content =
      fs.readFileSync(
        localPath,
        'utf8'
      );


    return {
      ok: true,

      async json() {
        return JSON.parse(
          content
        );
      }
    };
  };


vm.runInThisContext(
  growthSource,
  {
    filename:
      'assets/growth-tools.js'
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
    'growth-sex',
    'male'
  );

  set(
    'growth-age',
    '1001'
  );

  set(
    'growth-age-unit',
    'days'
  );

  set(
    'growth-age-basis',
    'chronological'
  );

  set(
    'growth-weight',
    '18'
  );

  set(
    'growth-lenhei',
    '120'
  );

  set(
    'growth-position',
    'height'
  );

  set(
    'growth-head',
    ''
  );

  const oedema =
    set(
      'growth-oedema'
    );

  oedema.checked = false;

  const result =
    set(
      'growth-result'
    );


  await calculateGrowthTool(
    event
  );


  assert(
    result.innerHTML
      .includes('-2.39')
  );

  assert(
    result.innerHTML
      .includes('WHO')
  );

  assert(
    result.innerHTML
      .includes('Brasil · SISVAN')
  );

  assert(
    result.innerHTML
      .includes(
        'Resultado calculado localmente'
      )
  );


  assert.strictEqual(
    lastGrowthResult
      .indicators
      .weight_for_length_height
      .classification_who
      .code,
    'wasted'
  );


  assert.strictEqual(
    lastGrowthResult
      .indicators
      .weight_for_length_height
      .classification_br
      .code,
    'thinness'
  );


  // Language-only rerender, no recalculation.
  globalThis.ClinicalI18n = {
    getLanguage() {
      return 'en-GB';
    },

    t(key) {
      const messages = {
        'growth.results':
          'Growth results',

        'growth.wfa':
          'Weight for age',

        'growth.hfa':
          'Length / height for age',

        'growth.wflh':
          'Weight for length / height',

        'growth.bfa':
          'BMI for age',

        'growth.hcfa':
          'Head circumference for age',

        'growth.z':
          'Z-score',

        'growth.percentile':
          'Percentile',

        'growth.percentileUnavailable':
          'Unavailable outside ±3 SD',

        'growth.who':
          'WHO',

        'growth.brazil':
          'Brazil · SISVAN',

        'growth.noNamedClass':
          'No additional named classification',

        'growth.warning':
          'Notes / warnings',

        'growth.adjustment':
          'Measurement-position adjustment',

        'growth.bmi':
          'Calculated BMI',

        'growth.offline':
          'Result calculated locally using the precached WHO tables.',

        'growth.invalid':
          'Enter sex, a valid age and at least one anthropometric measurement.',

        'growth.positionRequired':
          'Specify whether the measurement was recumbent length or standing height.'
      };

      return messages[key]
        || key;
    }
  };


  renderGrowthResult(
    lastGrowthResult,
    lastGrowthSource
  );


  assert(
    result.innerHTML
      .includes('Wasted')
  );

  assert(
    result.innerHTML
      .includes('Thinness')
  );

  assert(
    result.innerHTML
      .includes(
        'Result calculated locally'
      )
  );


  // Explicit corrected-age path.
  elements.get(
    'growth-age'
  ).value = '300';

  elements.get(
    'growth-age-unit'
  ).value = 'days';

  elements.get(
    'growth-age-basis'
  ).value = 'corrected';

  elements.get(
    'growth-weight'
  ).value = '8';

  elements.get(
    'growth-lenhei'
  ).value = '';

  elements.get(
    'growth-position'
  ).value = '';


  await calculateGrowthTool(
    event
  );


  assert.strictEqual(
    lastGrowthResult.age_basis,
    'corrected'
  );

  assert(
    result.innerHTML
      .includes(
        'Corrected age was used'
      )
  );


  // Empty anthropometry must fail closed.
  elements.get(
    'growth-weight'
  ).value = '';

  elements.get(
    'growth-head'
  ).value = '';


  await calculateGrowthTool(
    event
  );


  assert(
    result.innerHTML
      .includes(
        'Enter sex, a valid age and at least one anthropometric measurement.'
      )
  );


  console.log(
    'growth_ui_qc: bilingual API-first/offline WHO/SISVAN growth UI PASS'
  );

})().catch(
  error => {
    console.error(error);
    process.exit(1);
  }
);
