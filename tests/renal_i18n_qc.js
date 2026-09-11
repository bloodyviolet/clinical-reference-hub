const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const source = fs.readFileSync(
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

const vectors = JSON.parse(
  fs.readFileSync(
    'tests/fixtures/renal_vectors.json',
    'utf8'
  )
);


assert.strictEqual(
  typeof ClinicalTools.calculateEgfrCkdEpi2021,
  'function'
);

assert.strictEqual(
  typeof ClinicalTools.classifyCkd,
  'function'
);

assert.strictEqual(
  typeof ClinicalTools.calculateKdigoAki,
  'function'
);


for (
  const vector
  of vectors.egfr_nkf_verification
) {
  const result =
    ClinicalTools
      .calculateEgfrCkdEpi2021({
        age_years:
          vector.age_years,

        sex:
          vector.sex,

        serum_creatinine:
          vector.serum_creatinine,

        creatinine_unit:
          'mg/dL'
      });

  // The application contract returns one decimal.
  // Do not apply JavaScript Math.round() to that display value:
  // Math.round(128.5) differs from Python's ties-to-even round().
  assert.strictEqual(
    result.egfr_ml_min_1_73m2,
    vector.expected_1dp,
    `${vector.age_years}/${vector.sex}/${vector.serum_creatinine}: 1dp`
  );

  // NKF Table S1 publishes whole-number verification values.
  assert(
    Math.abs(
      result.egfr_ml_min_1_73m2
      - vector.expected_rounded
    ) <= 0.5,
    `${vector.age_years}/${vector.sex}/${vector.serum_creatinine}: NKF whole-number verification`
  );

  assert.strictEqual(
    result.race_coefficient_used,
    false
  );

  assert(
    result.gfr_category_label_pt
  );

  assert(
    result.gfr_category_label_en
  );

  assert(
    result.interpretation_pt
  );

  assert(
    result.interpretation_en
  );
}


const mg =
  ClinicalTools
    .calculateEgfrCkdEpi2021({
      age_years: 18,
      sex: 'male',
      serum_creatinine: 0.9,
      creatinine_unit: 'mg/dL'
    });


const si =
  ClinicalTools
    .calculateEgfrCkdEpi2021({
      age_years: 18,
      sex: 'male',
      serum_creatinine: 79.56,
      creatinine_unit: 'umol/L'
    });


assert.strictEqual(
  mg.egfr_ml_min_1_73m2,
  si.egfr_ml_min_1_73m2
);


for (
  const vector
  of vectors.ckd
) {
  const result =
    ClinicalTools.classifyCkd(
      vector.input
    );

  assert.strictEqual(
    result.ga_classification,
    vector.ga,
    vector.name
  );

  assert.strictEqual(
    result.ckd_status_code,
    vector.status,
    vector.name
  );

  assert(
    result.ckd_status_pt
  );

  assert(
    result.ckd_status_en
  );

  assert(
    result.classification_note_pt
  );

  assert(
    result.classification_note_en
  );
}


for (
  const vector
  of vectors.aki
) {
  const result =
    ClinicalTools.calculateKdigoAki(
      vector.input
    );

  assert.strictEqual(
    result.stage,
    vector.stage,
    vector.name
  );

  assert(
    result.interpretation_pt
  );

  assert(
    result.interpretation_en
  );

  assert.strictEqual(
    result.criteria_pt.length,
    result.criteria_en.length
  );
}


// Floating-point clinical threshold regression:
// 1.2 - 0.9 is slightly below 0.3 in IEEE-754,
// but clinically it is the exact 0.3 mg/dL cut-point.
const deltaBoundary =
  ClinicalTools.calculateKdigoAki({
    current_creatinine: 1.2,
    current_creatinine_unit: 'mg/dL',

    baseline_creatinine: 0.9,
    baseline_creatinine_unit: 'mg/dL',

    baseline_interval_hours: 24,

    weight_kg: null,
    urine_output_ml: null,
    urine_output_duration_hours: null,

    anuria_duration_hours: null,

    renal_replacement_therapy: false
  });


assert.strictEqual(
  deltaBoundary.stage,
  1
);


const belowDelta =
  ClinicalTools.calculateKdigoAki({
    current_creatinine: 1.199999,
    current_creatinine_unit: 'mg/dL',

    baseline_creatinine: 0.9,
    baseline_creatinine_unit: 'mg/dL',

    baseline_interval_hours: 24,

    weight_kg: null,
    urine_output_ml: null,
    urine_output_duration_hours: null,

    anuria_duration_hours: null,

    renal_replacement_therapy: false
  });


assert.strictEqual(
  belowDelta.stage,
  0
);


console.log(
  'renal_i18n_qc: CKD-EPI/KDIGO browser parity PASS'
);


const urineOnlyAki =
  ClinicalTools.calculateKdigoAki({
    current_creatinine: null,
    current_creatinine_unit: 'mg/dL',

    baseline_creatinine: null,
    baseline_creatinine_unit: null,
    baseline_interval_hours: null,

    weight_kg: 70,
    urine_output_ml: 200,
    urine_output_duration_hours: 6,

    anuria_duration_hours: null,

    renal_replacement_therapy: false
  });


assert.strictEqual(
  urineOnlyAki.stage,
  1
);

assert.strictEqual(
  urineOnlyAki.current_creatinine_mg_dl,
  null
);


const rrtOnlyAki =
  ClinicalTools.calculateKdigoAki({
    current_creatinine: null,
    current_creatinine_unit: 'mg/dL',

    baseline_creatinine: null,
    baseline_creatinine_unit: null,
    baseline_interval_hours: null,

    weight_kg: null,
    urine_output_ml: null,
    urine_output_duration_hours: null,

    anuria_duration_hours: null,

    renal_replacement_therapy: true
  });


assert.strictEqual(
  rrtOnlyAki.stage,
  3
);

assert.strictEqual(
  rrtOnlyAki.current_creatinine_mg_dl,
  null
);


assert.throws(
  () =>
    ClinicalTools.calculateKdigoAki({
      current_creatinine: null,
      current_creatinine_unit: 'mg/dL',

      baseline_creatinine: 1.0,
      baseline_creatinine_unit: 'mg/dL',
      baseline_interval_hours: 24,

      weight_kg: null,
      urine_output_ml: null,
      urine_output_duration_hours: null,

      anuria_duration_hours: null,

      renal_replacement_therapy: false
    }),

  /current_creatinine_required_with_baseline/
);


console.log(
  'renal_i18n_qc: optional-creatinine AKI paths PASS'
);
