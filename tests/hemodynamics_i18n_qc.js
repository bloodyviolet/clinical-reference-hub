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
