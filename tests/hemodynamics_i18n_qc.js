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
      'tests/fixtures/hemodynamics_vectors.json',
      'utf8'
    )
  );


assert.strictEqual(
  typeof ClinicalTools
    .calculateHemodynamics,
  'function'
);


for (const vector of vectors) {
  const result =
    ClinicalTools
      .calculateHemodynamics(
        vector.input
      );


  assert.strictEqual(
    result.pulse_pressure_mm_hg,
    vector.pulse_pressure,
    `${vector.name}: PP`
  );


  assert.strictEqual(
    result.mean_arterial_pressure_mm_hg,
    vector.map,
    `${vector.name}: MAP`
  );


  assert.strictEqual(
    result.shock_index,
    vector.shock_index,
    `${vector.name}: SI`
  );


  assert.strictEqual(
    result.modified_shock_index,
    vector.modified_shock_index,
    `${vector.name}: MSI`
  );


  assert.strictEqual(
    result.threshold_classification_applied,
    false
  );


  assert(
    result.interpretation_pt
  );

  assert(
    result.interpretation_en
  );

  assert(
    result.map_note_pt
  );

  assert(
    result.map_note_en
  );
}


assert.throws(
  () =>
    ClinicalTools
      .calculateHemodynamics({
        systolic_bp: 70,
        diastolic_bp: 80,
        heart_rate: 60
      }),

  /systolic_below_diastolic/
);


console.log(
  'hemodynamics_i18n_qc: MAP/PP/SI/MSI parity PASS'
);


const genericContext =
  ClinicalTools
    .calculateHemodynamics({
      systolic_bp: 85,
      diastolic_bp: 55,
      heart_rate: 90
    });


assert.strictEqual(
  genericContext.clinical_context,
  'none'
);

assert.strictEqual(
  genericContext
    .brazil_context_guidance_applied,
  false
);

assert.strictEqual(
  genericContext
    .threshold_classification_applied,
  false
);

assert.strictEqual(
  genericContext
    .universal_threshold_inference_applied,
  false
);


const septicContext =
  ClinicalTools
    .calculateHemodynamics({
      systolic_bp: 85,
      diastolic_bp: 55,
      heart_rate: 90,
      clinical_context:
        'septic_shock'
    });


assert.strictEqual(
  septicContext
    .mean_arterial_pressure_mm_hg,
  65.0
);

assert.strictEqual(
  septicContext
    .brazil_context_rule_code,
  'septic_shock_map_target'
);

assert.strictEqual(
  septicContext
    .brazil_context_operator,
  '>='
);

assert.strictEqual(
  septicContext
    .brazil_context_rule_met,
  true
);


const obstetricExact =
  ClinicalTools
    .calculateHemodynamics({
      systolic_bp: 100,
      diastolic_bp: 70,
      heart_rate: 90,
      clinical_context:
        'obstetric_hemorrhage'
    });


assert.strictEqual(
  obstetricExact.shock_index,
  0.9
);

assert.strictEqual(
  obstetricExact
    .brazil_context_operator,
  '>'
);

assert.strictEqual(
  obstetricExact
    .brazil_context_rule_met,
  false
);


const obstetricAbove =
  ClinicalTools
    .calculateHemodynamics({
      systolic_bp: 100,
      diastolic_bp: 70,
      heart_rate: 91,
      clinical_context:
        'obstetric_hemorrhage'
    });


assert.strictEqual(
  obstetricAbove.shock_index,
  0.91
);

assert.strictEqual(
  obstetricAbove
    .brazil_context_rule_met,
  true
);

assert.strictEqual(
  obstetricAbove
    .threshold_classification_applied,
  false
);


assert.throws(
  () =>
    ClinicalTools
      .calculateHemodynamics({
        systolic_bp: 120,
        diastolic_bp: 80,
        heart_rate: 60,
        clinical_context:
          'generic_shock'
      }),

  /invalid_hemodynamic_context/
);


console.log(
  'hemodynamics_i18n_qc: Brazil context-gated parity PASS'
);
