const fs = require('fs');
const vm = require('vm');
const assert = require('assert');


const source =
  fs.readFileSync(
    'assets/clinical-tools.js',
    'utf8'
  );


vm.runInThisContext(
  source,
  {
    filename:
      'assets/clinical-tools.js'
  }
);


const vectors =
  JSON.parse(
    fs.readFileSync(
      'tests/fixtures/oxygenation_vectors.json',
      'utf8'
    )
  );


assert.strictEqual(
  typeof ClinicalTools
    .calculateOxygenation,
  'function'
);


for (const vector of vectors) {
  const result =
    ClinicalTools
      .calculateOxygenation(
        vector.input
      );


  assert.strictEqual(
    result.pf_ratio_mm_hg,
    vector.pf_ratio,
    `${vector.name}: P/F`
  );


  assert.strictEqual(
    result.sf_ratio,
    vector.sf_ratio,
    `${vector.name}: S/F`
  );


  assert.strictEqual(
    result.sf_spo2_above_97_caution,
    vector.sf_caution,
    `${vector.name}: S/F caution`
  );


  assert.strictEqual(
    result.global_ards_sf_threshold_applicable,
    vector.sf_threshold_applicable,
    `${vector.name}: Global ARDS S/F applicability`
  );


  assert.strictEqual(
    result.ards_classification_applied,
    false
  );


  assert(
    result.interpretation_pt
  );

  assert(
    result.interpretation_en
  );

  assert(
    result.fio2_note_pt
  );

  assert(
    result.fio2_note_en
  );
}


assert.throws(
  () =>
    ClinicalTools
      .calculateOxygenation({
        fio2_percent: 40,
        pao2_mm_hg: null,
        spo2_percent: null
      }),

  /oxygenation_measurement_required/
);


assert.throws(
  () =>
    ClinicalTools
      .calculateOxygenation({
        fio2_percent: 0.4,
        pao2_mm_hg: 80,
        spo2_percent: 95
      }),

  /invalid_fio2/
);


console.log(
  'oxygenation_i18n_qc: P/F + S/F browser parity PASS'
);
