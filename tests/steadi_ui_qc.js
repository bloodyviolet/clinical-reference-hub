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


for (const id of [
  'steadi-tug-form',
  'steadi-chair-form',
  'steadi-balance-form',
  'steadi-orthostatic-form'
]) {
  assert(
    html.includes(
      `id="${id}"`
    )
  );
}


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

    dataset:
      {},

    className:
      '',

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
    'steadi.offline':
      'Resultado calculado localmente em modo offline.',

    'steadi.tug.resultTitle':
      'Resultado · TUG STEADI',

    'steadi.tug.increased':
      'Critério STEADI de risco aumentado atingido (≥12 s).',

    'steadi.tug.notIncreased':
      'Critério STEADI de risco aumentado não atingido (<12 s).',

    'steadi.tug.boundary':
      'TUG não é o item de marcha de 4 metros do IVCF-20.',

    'steadi.chair.resultTitle':
      'Resultado · 30-Second Chair Stand',

    'steadi.chair.raw':
      'Repetições registradas',

    'steadi.chair.below':
      'Abaixo da média de referência STEADI.',

    'steadi.chair.notBelow':
      'Não está abaixo da média de referência STEADI.',

    'steadi.chair.unavailable':
      'A tabela STEADI não fornece classificação idade/sexo para esta idade.',

    'steadi.chair.armZero':
      'Quando os braços são necessários para levantar, o protocolo orienta interromper o teste e registrar zero.',

    'steadi.chair.noExtrapolation':
      'Após 94 anos, preserve o resultado bruto; não extrapole o ponto de corte.',

    'steadi.balance.resultTitle':
      'Resultado · 4-Stage Balance',

    'steadi.balance.increased':
      'Tandem por menos de 10 s / não alcançado: critério STEADI de risco aumentado.',

    'steadi.balance.notIncreased':
      'Tandem mantido por 10 s: critério específico STEADI de risco aumentado não atingido.',

    'steadi.balance.noDevice':
      'O protocolo STEADI de 4 estágios não permite dispositivo de auxílio durante o teste.',

    'steadi.ortho.resultTitle':
      'Resultado · pressão ortostática STEADI',

    'steadi.ortho.abnormal':
      'Avaliação STEADI anormal: queda de PAS ≥20 mmHg, queda de PAD ≥10 mmHg e/ou sintomas.',

    'steadi.ortho.normal':
      'Critérios STEADI de anormalidade não atingidos.',

    'steadi.ortho.sbpDrop':
      'Maior queda de PAS',

    'steadi.ortho.dbpDrop':
      'Maior queda de PAD',

    'steadi.ortho.noPulseThreshold':
      'O pulso é registrado, mas nenhum limiar de pulso é inventado por esta ferramenta.',

    'steadi.ortho.boundary':
      'O protocolo 5/1/3 min e os critérios 20/10 mmHg são STEADI complementar.'
  },

  'en-GB': {
    'steadi.offline':
      'Result calculated locally while offline.',

    'steadi.tug.resultTitle':
      'Result · STEADI TUG',

    'steadi.tug.increased':
      'STEADI increased-risk criterion reached (≥12 s).',

    'steadi.tug.notIncreased':
      'STEADI increased-risk criterion not reached (<12 s).',

    'steadi.tug.boundary':
      'TUG is not the IVCF-20 4-metre gait item.',

    'steadi.chair.resultTitle':
      'Result · 30-Second Chair Stand',

    'steadi.chair.raw':
      'Recorded repetitions',

    'steadi.chair.below':
      'Below the STEADI reference average.',

    'steadi.chair.notBelow':
      'Not below the STEADI reference average.',

    'steadi.chair.unavailable':
      'The STEADI table provides no age/sex classification for this age.',

    'steadi.chair.armZero':
      'When the arms are required to stand, the protocol instructs the examiner to stop and record zero.',

    'steadi.chair.noExtrapolation':
      'After age 94, preserve the raw result; do not extrapolate a cutoff.',

    'steadi.balance.resultTitle':
      'Result · 4-Stage Balance',

    'steadi.balance.increased':
      'Tandem held for less than 10 s / not reached: STEADI increased-risk criterion.',

    'steadi.balance.notIncreased':
      'Tandem held for 10 s: the STEADI tandem-specific increased-risk criterion was not reached.',

    'steadi.balance.noDevice':
      'The STEADI 4-Stage Balance protocol does not permit an assistive device during the test.',

    'steadi.ortho.resultTitle':
      'Result · STEADI orthostatic BP',

    'steadi.ortho.abnormal':
      'Abnormal STEADI assessment: SBP drop ≥20 mmHg, DBP drop ≥10 mmHg and/or symptoms.',

    'steadi.ortho.normal':
      'STEADI abnormality criteria were not reached.',

    'steadi.ortho.sbpDrop':
      'Maximum SBP drop',

    'steadi.ortho.dbpDrop':
      'Maximum DBP drop',

    'steadi.ortho.noPulseThreshold':
      'Pulse is recorded, but this tool does not invent a pulse threshold.',

    'steadi.ortho.boundary':
      'The 5/1/3-minute protocol and 20/10-mmHg criteria are complementary STEADI guidance.'
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


let fetchMode =
  'offline';

let fetchUrls =
  [];


global.fetch =
  async function steadiFetch(
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
          '/steadi-tug'
        )
    ) {
      result =
        ClinicalTools
          .calculateSteadiTug(
            payload
          );

    } else if (
      String(url)
        .endsWith(
          '/steadi-chair-stand-30s'
        )
    ) {
      result =
        ClinicalTools
          .calculateSteadiChairStand30s(
            payload
          );

    } else if (
      String(url)
        .endsWith(
          '/steadi-four-stage-balance'
        )
    ) {
      result =
        ClinicalTools
          .calculateSteadiFourStageBalance(
            payload
          );

    } else if (
      String(url)
        .endsWith(
          '/steadi-orthostatic-bp'
        )
    ) {
      result =
        ClinicalTools
          .calculateSteadiOrthostaticBp(
            payload
          );

    } else {
      throw new Error(
        `unexpected URL: ${url}`
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
  // TUG — offline fallback.
  // ---------------------------------------------------------------

  set(
    'steadi-tug-time',
    '12'
  );

  set(
    'steadi-tug-walking-aid',
    'true'
  );

  set(
    'steadi-tug-protocol',
    'true'
  );

  const tugResult =
    set(
      'steadi-tug-result'
    );

  await calculateSteadiTugTool(
    event
  );

  assert(
    fetchUrls.includes(
      '/api/v1/tools/steadi-tug'
    )
  );

  assert.strictEqual(
    lastSteadiTugSource,
    'offline'
  );

  assert.strictEqual(
    lastSteadiTugResult
      .increased_fall_risk,
    true
  );

  assert.strictEqual(
    lastSteadiTugResult
      .walking_aid_used,
    true
  );

  assert.strictEqual(
    lastSteadiTugResult
      .ivcf_four_meter_gait_inferred,
    false
  );

  assert(
    tugResult.innerHTML
      .includes(
        'risco aumentado atingido'
      )
  );

  assert(
    tugResult.innerHTML
      .includes(
        'não é o item de marcha de 4 metros'
      )
  );

  assert(
    tugResult.innerHTML
      .includes(
        'modo offline'
      )
  );


  // ---------------------------------------------------------------
  // Chair Stand — age >94 must remain raw/unclassified.
  // ---------------------------------------------------------------

  set(
    'steadi-chair-age',
    '125'
  );

  set(
    'steadi-chair-sex',
    'female'
  );

  set(
    'steadi-chair-repetitions',
    '1'
  );

  set(
    'steadi-chair-arms',
    'false'
  );

  set(
    'steadi-chair-protocol',
    'true'
  );

  const chairResult =
    set(
      'steadi-chair-result'
    );

  await calculateSteadiChairStandTool(
    event
  );

  assert(
    fetchUrls.includes(
      '/api/v1/tools/steadi-chair-stand-30s'
    )
  );

  assert.strictEqual(
    lastSteadiChairSource,
    'offline'
  );

  assert.strictEqual(
    lastSteadiChairResult
      .age_years,
    125
  );

  assert.strictEqual(
    lastSteadiChairResult
      .reference_classification_available,
    false
  );

  assert.strictEqual(
    lastSteadiChairResult
      .below_average,
    null
  );

  assert.strictEqual(
    lastSteadiChairResult
      .increased_fall_risk,
    null
  );

  assert.strictEqual(
    lastSteadiChairResult
      .cutoff_extrapolated,
    false
  );

  assert(
    chairResult.innerHTML
      .includes(
        'não fornece classificação'
      )
  );

  assert(
    chairResult.innerHTML
      .includes(
        'Após 94 anos'
      )
  );


  // ---------------------------------------------------------------
  // 4-Stage — tandem <10.
  // ---------------------------------------------------------------

  set(
    'steadi-balance-side',
    '10'
  );

  set(
    'steadi-balance-semi',
    '10'
  );

  set(
    'steadi-balance-tandem',
    '9'
  );

  set(
    'steadi-balance-one-leg',
    ''
  );

  set(
    'steadi-balance-device',
    'false'
  );

  set(
    'steadi-balance-protocol',
    'true'
  );

  const balanceResult =
    set(
      'steadi-balance-result'
    );

  await calculateSteadiBalanceTool(
    event
  );

  assert(
    fetchUrls.includes(
      '/api/v1/tools/steadi-four-stage-balance'
    )
  );

  assert.strictEqual(
    lastSteadiBalanceSource,
    'offline'
  );

  assert.strictEqual(
    lastSteadiBalanceResult
      .tandem_held_10_seconds,
    false
  );

  assert.strictEqual(
    lastSteadiBalanceResult
      .increased_fall_risk,
    true
  );

  assert.strictEqual(
    lastSteadiBalanceResult
      .assistive_device_allowed,
    false
  );

  assert(
    balanceResult.innerHTML
      .includes(
        'Tandem por menos de 10 s'
      )
  );


  // ---------------------------------------------------------------
  // Orthostatic — exact 20/10 criteria.
  // ---------------------------------------------------------------

  set(
    'steadi-ortho-supine-sbp',
    '130'
  );

  set(
    'steadi-ortho-supine-dbp',
    '80'
  );

  set(
    'steadi-ortho-supine-pulse',
    '70'
  );

  set(
    'steadi-ortho-1m-sbp',
    '110'
  );

  set(
    'steadi-ortho-1m-dbp',
    '80'
  );

  set(
    'steadi-ortho-1m-pulse',
    '76'
  );

  set(
    'steadi-ortho-3m-sbp',
    '130'
  );

  set(
    'steadi-ortho-3m-dbp',
    '70'
  );

  set(
    'steadi-ortho-3m-pulse',
    '74'
  );

  set(
    'steadi-ortho-symptoms',
    'false'
  );

  set(
    'steadi-ortho-protocol',
    'true'
  );

  const orthoResult =
    set(
      'steadi-orthostatic-result'
    );

  await calculateSteadiOrthostaticTool(
    event
  );

  assert(
    fetchUrls.includes(
      '/api/v1/tools/steadi-orthostatic-bp'
    )
  );

  assert.strictEqual(
    lastSteadiOrthostaticSource,
    'offline'
  );

  assert.strictEqual(
    lastSteadiOrthostaticResult
      .maximum_systolic_drop_mm_hg,
    20
  );

  assert.strictEqual(
    lastSteadiOrthostaticResult
      .maximum_diastolic_drop_mm_hg,
    10
  );

  assert.strictEqual(
    lastSteadiOrthostaticResult
      .abnormal_steadi_orthostatic_assessment,
    true
  );

  assert.strictEqual(
    lastSteadiOrthostaticResult
      .fall_risk_classification_applied,
    false
  );

  assert(
    orthoResult.innerHTML
      .includes(
        'Avaliação STEADI anormal'
      )
  );

  assert(
    orthoResult.innerHTML
      .includes(
        'nenhum limiar de pulso'
      )
  );


  // ---------------------------------------------------------------
  // Language-only rerender must not recalculate.
  // ---------------------------------------------------------------

  const beforeLanguageRerender =
    fetchUrls.length;

  language =
    'en-GB';


  renderSteadiTugResult(
    lastSteadiTugResult,
    lastSteadiTugSource
  );

  renderSteadiChairResult(
    lastSteadiChairResult,
    lastSteadiChairSource
  );

  renderSteadiBalanceResult(
    lastSteadiBalanceResult,
    lastSteadiBalanceSource
  );

  renderSteadiOrthostaticResult(
    lastSteadiOrthostaticResult,
    lastSteadiOrthostaticSource
  );


  assert.strictEqual(
    fetchUrls.length,
    beforeLanguageRerender
  );


  assert(
    tugResult.innerHTML
      .includes(
        'increased-risk criterion reached'
      )
  );

  assert(
    tugResult.innerHTML
      .includes(
        'is not the IVCF-20 4-metre gait item'
      )
  );

  assert(
    chairResult.innerHTML
      .includes(
        'provides no age/sex classification'
      )
  );

  assert(
    chairResult.innerHTML
      .includes(
        'After age 94'
      )
  );

  assert(
    balanceResult.innerHTML
      .includes(
        'Tandem held for less than 10 s'
      )
  );

  assert(
    orthoResult.innerHTML
      .includes(
        'Abnormal STEADI assessment'
      )
  );

  assert(
    orthoResult.innerHTML
      .includes(
        'does not invent a pulse threshold'
      )
  );

  assert(
    orthoResult.innerHTML
      .includes(
        'Result calculated locally while offline.'
      )
  );


  // ---------------------------------------------------------------
  // Incomplete TUG must fail before fetch.
  // ---------------------------------------------------------------

  language =
    'pt-BR';

  elements.get(
    'steadi-tug-protocol'
  ).value = '';

  const beforeIncomplete =
    fetchUrls.length;

  await calculateSteadiTugTool(
    event
  );

  assert.strictEqual(
    fetchUrls.length,
    beforeIncomplete
  );

  assert(
    tugResult.innerHTML
      .includes(
        'confirmação do protocolo'
      )
  );


  // ---------------------------------------------------------------
  // API path proof.
  // ---------------------------------------------------------------

  elements.get(
    'steadi-tug-protocol'
  ).value = 'true';

  fetchMode =
    'api';

  await calculateSteadiTugTool(
    event
  );

  assert.strictEqual(
    lastSteadiTugSource,
    'api'
  );

  assert.strictEqual(
    lastSteadiTugResult
      .increased_fall_risk,
    true
  );

  assert(
    !tugResult.innerHTML
      .includes(
        'modo offline'
      )
  );


  console.log(
    'steadi_ui_qc: bilingual API-first/offline STEADI UI PASS'
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
