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


const html =
  fs.readFileSync(
    'index.html',
    'utf8'
  );


assert(
  html.includes(
    'id="caderneta-falls-form"'
  )
);


assert(
  html.includes(
    'id="ivcf20-form"'
  )
);


const FALL_KEYS = [
  'fall_previous_year',
  'cane_or_walker_recommended',
  'unsteady_while_walking',
  'uses_furniture_for_support',
  'concern_about_falling',
  'needs_hands_to_rise_from_chair',
  'difficulty_stepping_onto_curb',
  'toilet_urgency',
  'reduced_foot_sensation',
  'medication_dizziness_or_fatigue',
  'sleep_or_mood_medication',
  'sadness_or_depressed_mood'
];


const IVCF_KEYS = [
  'self_rated_health_regular_or_poor',
  'stopped_shopping_due_health',
  'stopped_managing_money_due_health',
  'stopped_housework_due_health',
  'stopped_bathing_due_health',
  'forgetfulness_noted_by_others',
  'worsening_forgetfulness',
  'forgetfulness_impairs_daily_activity',
  'depressed_or_hopeless_last_month',
  'anhedonia_last_month',
  'unable_raise_arms_above_shoulders',
  'unable_handle_small_objects',
  'unintentional_weight_loss_criterion',
  'bmi_lt_22',
  'calf_circumference_lt_31_cm',
  'gait_4m_gt_5_seconds',
  'walking_difficulty_impairs_daily_activity',
  'two_or_more_falls_last_year',
  'urinary_or_fecal_incontinence',
  'vision_impairs_daily_activity',
  'hearing_impairs_daily_activity',
  'five_or_more_chronic_conditions',
  'five_or_more_daily_medications',
  'hospitalized_last_six_months'
];


const elements =
  new Map();


function makeElement(
  value = ''
) {
  return {
    value,
    checked:
      false,
    innerHTML:
      '',
    textContent:
      '',
    className:
      '',
    dataset:
      {},

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


function idFor(
  prefix,
  field
) {
  return (
    `${prefix}-`
    + field.replace(
        /_/g,
        '-'
      )
  );
}


function setBooleanFields(
  prefix,
  fields,
  overrides = {}
) {
  for (const field of fields) {
    set(
      idFor(
        prefix,
        field
      ),
      Object.hasOwn(
        overrides,
        field
      )
        ? (
            overrides[field]
              ? 'true'
              : 'false'
          )
        : 'false'
    );
  }
}


global.document = {
  getElementById(id) {
    if (!elements.has(id)) {
      elements.set(
        id,
        makeElement()
      );
    }

    return elements.get(
      id
    );
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


const translation = {
  'pt-BR': {
    'falls.resultTitle':
      'Resultado · check-up de quedas',

    'falls.positiveCount':
      'Respostas positivas',

    'falls.assessmentYes':
      'Há resposta positiva: realizar/orientar avaliação.',

    'falls.assessmentNo':
      'Nenhuma resposta positiva registrada.',

    'falls.noScore':
      'Este check-up não gera escore ponderado e não importa pontuação STEADI/NCOA.',

    'falls.offline':
      'Resultado calculado localmente em modo offline.',

    'ivcf.resultTitle':
      'Resultado · IVCF-20',

    'ivcf.total':
      'Pontuação total',

    'ivcf.classification':
      'Vulnerabilidade clínico-funcional',

    'ivcf.reapply':
      'Reaplicação mínima',

    'ivcf.reapply12':
      'Pelo menos a cada 12 meses.',

    'ivcf.reapply6':
      'Pelo menos a cada 6 meses.',

    'ivcf.alteredDomains':
      'Dimensões com pontuação',

    'ivcf.noFallsScore':
      'O IVCF-20 não deve ser apresentado como escore isolado de risco de quedas e não deve ser somado ao check-up da Caderneta.',

    'ivcf.gaitNotTug':
      'O item de marcha de 4 metros >5 segundos pertence ao IVCF-20 e NÃO é Timed Up and Go (TUG).',

    'ivcf.sentinel':
      'Evento sentinela, incluindo queda, indica nova avaliação independentemente da pontuação.',

    'ivcf.offline':
      'IVCF-20 calculado localmente em modo offline.'
  },

  'en-GB': {
    'falls.resultTitle':
      'Result · falls check-up',

    'falls.positiveCount':
      'Positive responses',

    'falls.assessmentYes':
      'At least one positive response: assessment is indicated.',

    'falls.assessmentNo':
      'No positive response was recorded.',

    'falls.noScore':
      'This check-up does not produce a weighted score and does not import STEADI/NCOA scoring.',

    'falls.offline':
      'Result calculated locally while offline.',

    'ivcf.resultTitle':
      'Result · IVCF-20',

    'ivcf.total':
      'Total score',

    'ivcf.classification':
      'Clinical-functional vulnerability',

    'ivcf.reapply':
      'Minimum reapplication',

    'ivcf.reapply12':
      'At least every 12 months.',

    'ivcf.reapply6':
      'At least every 6 months.',

    'ivcf.alteredDomains':
      'Scoring dimensions',

    'ivcf.noFallsScore':
      'IVCF-20 must not be presented as a standalone falls-risk score and must not be added to the Caderneta check-up.',

    'ivcf.gaitNotTug':
      'The IVCF-20 4-metre gait item >5 seconds is NOT the Timed Up and Go (TUG).',

    'ivcf.sentinel':
      'A sentinel event, including a fall, indicates reassessment irrespective of the score.',

    'ivcf.offline':
      'IVCF-20 calculated locally while offline.'
  }
};


globalThis.ClinicalI18n = {
  getLanguage() {
    return language;
  },

  t(key) {
    return (
      translation[
        language
      ][key]
      || key
    );
  }
};


let fetchUrls =
  [];


let fetchMode =
  'offline';


global.fetch =
  async function item7Fetch(
    url,
    options
  ) {
    fetchUrls.push(
      String(url)
    );

    if (
      fetchMode === 'offline'
    ) {
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
      String(url)
        .endsWith(
          '/brazil-caderneta-falls'
        )
    ) {
      result =
        ClinicalTools
          .calculateCadernetaFallsCheckup(
            payload
          );
    } else {
      result =
        ClinicalTools
          .calculateIvcf20(
            payload
          );
    }

    return {
      ok:
        true,

      async json() {
        return result;
      }
    };
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

  // ---------------------------------------------------------------
  // Caderneta — API-first then local fallback.
  // ---------------------------------------------------------------

  set(
    'caderneta-falls-age',
    '125'
  );


  setBooleanFields(
    'caderneta-falls',
    FALL_KEYS,
    {
      concern_about_falling:
        true
    }
  );


  const fallsResult =
    set(
      'caderneta-falls-result'
    );


  await calculateCadernetaFallsTool(
    event
  );


  assert(
    fetchUrls.includes(
      '/api/v1/tools/brazil-caderneta-falls'
    )
  );


  assert.strictEqual(
    lastCadernetaFallsSource,
    'offline'
  );


  assert.strictEqual(
    lastCadernetaFallsResult
      .age_years,
    125
  );


  assert.strictEqual(
    lastCadernetaFallsResult
      .positive_items_count,
    1
  );


  assert.strictEqual(
    lastCadernetaFallsResult
      .assessment_indicated,
    true
  );


  assert.strictEqual(
    lastCadernetaFallsResult
      .weighted_score_applied,
    false
  );


  assert.strictEqual(
    lastCadernetaFallsResult
      .foreign_weighted_score_imported,
    false
  );


  assert.strictEqual(
    lastCadernetaFallsResult
      .automatic_ivcf_inference_applied,
    false
  );


  assert.strictEqual(
    lastCadernetaFallsResult
      .synthetic_cross_instrument_score_applied,
    false
  );


  assert(
    fallsResult.innerHTML
      .includes(
        '1/12'
      )
  );


  assert(
    fallsResult.innerHTML
      .includes(
        'realizar/orientar avaliação'
      )
  );


  assert(
    fallsResult.innerHTML
      .includes(
        'Resultado calculado localmente'
      )
  );


  // Language-only rerender — no calculation.
  const beforeRerenderFetches =
    fetchUrls.length;


  language =
    'en-GB';


  renderCadernetaFallsResult(
    lastCadernetaFallsResult,
    lastCadernetaFallsSource
  );


  assert.strictEqual(
    fetchUrls.length,
    beforeRerenderFetches
  );


  assert(
    fallsResult.innerHTML
      .includes(
        'assessment is indicated'
      )
  );


  assert(
    fallsResult.innerHTML
      .includes(
        'does not produce a weighted score'
      )
  );


  assert(
    fallsResult.innerHTML
      .includes(
        'Result calculated locally while offline.'
      )
  );


  // Incomplete Caderneta must fail before API/offline engine.
  language =
    'pt-BR';


  elements.get(
    idFor(
      'caderneta-falls',
      'sadness_or_depressed_mood'
    )
  ).value = '';


  const beforeIncompleteFalls =
    fetchUrls.length;


  await calculateCadernetaFallsTool(
    event
  );


  assert.strictEqual(
    fetchUrls.length,
    beforeIncompleteFalls
  );


  assert(
    fallsResult.innerHTML
      .includes(
        'todos os 12 itens'
      )
  );


  // Restore complete field.
  elements.get(
    idFor(
      'caderneta-falls',
      'sadness_or_depressed_mood'
    )
  ).value = 'false';


  // ---------------------------------------------------------------
  // IVCF-20 — complete assessment and local fallback.
  // ---------------------------------------------------------------

  set(
    'ivcf20-age',
    '85'
  );


  setBooleanFields(
    'ivcf20',
    IVCF_KEYS,
    {
      self_rated_health_regular_or_poor:
        true,

      stopped_bathing_due_health:
        true
    }
  );


  const ivcfResult =
    set(
      'ivcf20-result'
    );


  await calculateIvcf20Tool(
    event
  );


  assert(
    fetchUrls.includes(
      '/api/v1/tools/ivcf20'
    )
  );


  assert.strictEqual(
    lastIvcf20Source,
    'offline'
  );


  // Age 85 = 3, health perception = 1, bathing = 6.
  assert.strictEqual(
    lastIvcf20Result
      .total_score,
    10
  );


  assert.strictEqual(
    lastIvcf20Result
      .classification_code,
    'moderate'
  );


  assert.strictEqual(
    lastIvcf20Result
      .reapplication_months_minimum,
    6
  );


  assert.strictEqual(
    lastIvcf20Result
      .gait_4m_is_tug,
    false
  );


  assert.strictEqual(
    lastIvcf20Result
      .fall_risk_classification_applied,
    false
  );


  assert.strictEqual(
    lastIvcf20Result
      .automatic_caderneta_inference_applied,
    false
  );


  assert.strictEqual(
    lastIvcf20Result
      .synthetic_cross_instrument_score_applied,
    false
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        '10/40'
      )
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'Moderado risco de vulnerabilidade'
      )
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'NÃO é Timed Up and Go'
      )
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'não deve ser somado ao check-up'
      )
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'IVCF-20 calculado localmente'
      )
  );


  // English rerender without recalculation.
  const beforeIvcfRerender =
    fetchUrls.length;


  language =
    'en-GB';


  renderIvcf20Result(
    lastIvcf20Result,
    lastIvcf20Source
  );


  assert.strictEqual(
    fetchUrls.length,
    beforeIvcfRerender
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'Moderate clinical-functional'
      )
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'must not be presented as a standalone falls-risk score'
      )
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'is NOT the Timed Up and Go'
      )
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'calculated locally while offline'
      )
  );


  // Incomplete IVCF-20 must fail before fetch.
  language =
    'pt-BR';


  elements.get(
    idFor(
      'ivcf20',
      'hearing_impairs_daily_activity'
    )
  ).value = '';


  const beforeIncompleteIvcf =
    fetchUrls.length;


  await calculateIvcf20Tool(
    event
  );


  assert.strictEqual(
    fetchUrls.length,
    beforeIncompleteIvcf
  );


  assert(
    ivcfResult.innerHTML
      .includes(
        'todos os itens do IVCF-20'
      )
  );


  // Restore completeness and prove the online/API result path.
  elements.get(
    idFor(
      'ivcf20',
      'hearing_impairs_daily_activity'
    )
  ).value = 'false';


  fetchMode =
    'api';


  await calculateIvcf20Tool(
    event
  );


  assert.strictEqual(
    lastIvcf20Source,
    'api'
  );


  assert.strictEqual(
    lastIvcf20Result
      .total_score,
    10
  );


  assert(
    !ivcfResult.innerHTML
      .includes(
        'modo offline'
      )
  );


  console.log(
    'falls_function_ui_qc: bilingual API-first/offline Caderneta + IVCF-20 UI PASS'
  );

})().catch(
  error => {
    console.error(
      error
    );

    process.exit(
      1
    );
  }
);
