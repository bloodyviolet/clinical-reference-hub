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
      'tests/fixtures/metabolic_vectors.json',
      'utf8'
    )
  );


assert.strictEqual(
  typeof ClinicalTools
    .calculateMetabolicToolkit,
  'function'
);


for (const vector of vectors) {
  const result =
    ClinicalTools
      .calculateMetabolicToolkit(
        vector.input
      );


  assert.strictEqual(
    result.anion_gap_meq_l,
    vector.anion_gap,
    `${vector.name}: AG`
  );


  assert.strictEqual(
    result.albumin_corrected_anion_gap_meq_l,
    vector.corrected_anion_gap,
    `${vector.name}: corrected AG`
  );


  assert.strictEqual(
    result.calculated_osmolality_mosm_kg,
    vector.osmolality,
    `${vector.name}: osmolality`
  );


  assert.strictEqual(
    result.corrected_sodium_meq_l,
    vector.corrected_sodium,
    `${vector.name}: corrected sodium`
  );


  assert.strictEqual(
    result.delta_ratio,
    vector.delta_ratio,
    `${vector.name}: delta`
  );


  if (
    Object.hasOwn(
      vector,
      'winter_expected'
    )
  ) {
    assert.strictEqual(
      result.winter_expected_paco2_mm_hg,
      vector.winter_expected,
      `${vector.name}: Winter`
    );

    assert.strictEqual(
      result.winter_compensation_status,
      vector.winter_status,
      `${vector.name}: Winter status`
    );
  }


  assert(
    result.interpretation_pt
  );

  assert(
    result.interpretation_en
  );
}


// Exact validity boundaries must not accidentally
// cross because of floating-point representation.
const exactAgBoundary =
  ClinicalTools
    .calculateMetabolicToolkit({
      sodium_meq_l: 140,
      chloride_meq_l: 112,
      bicarbonate_meq_l: 16,
      albumin_g_dl: null,
      glucose_mg_dl: null,
      bun_mg_dl: null,
      paco2_mm_hg: null,
      metabolic_acidosis_confirmed: true
    });


assert.strictEqual(
  exactAgBoundary.anion_gap_meq_l,
  12
);

assert.strictEqual(
  exactAgBoundary.delta_analysis_applied,
  false
);


const exactBicarbBoundary =
  ClinicalTools
    .calculateMetabolicToolkit({
      sodium_meq_l: 140,
      chloride_meq_l: 104,
      bicarbonate_meq_l: 24,
      albumin_g_dl: null,
      glucose_mg_dl: null,
      bun_mg_dl: null,
      paco2_mm_hg: 40,
      metabolic_acidosis_confirmed: true
    });


assert.strictEqual(
  exactBicarbBoundary.winter_analysis_applied,
  false
);

assert.strictEqual(
  exactBicarbBoundary.delta_analysis_applied,
  false
);


assert.throws(
  () =>
    ClinicalTools
      .calculateMetabolicToolkit({
        sodium_meq_l: 140,
        chloride_meq_l: 104,
        bicarbonate_meq_l: null,
        albumin_g_dl: null,
        glucose_mg_dl: null,
        bun_mg_dl: null,
        paco2_mm_hg: null,
        metabolic_acidosis_confirmed: false
      }),

  /chloride_bicarbonate_required_together/
);


console.log(
  'metabolic_i18n_qc: AG/osmolality/corrected-Na/Winter/delta parity PASS'
);


assert.strictEqual(
  typeof ClinicalTools
    .calculateBrazilMethanolContext,
  'function'
);


assert.throws(
  () =>
    ClinicalTools
      .calculateBrazilMethanolContext({
        explicit_methanol_context:
          false,
        sodium_mmol_l:
          140,
        potassium_mmol_l:
          4,
        chloride_mmol_l:
          104,
        bicarbonate_mmol_l:
          20
      }),

  /methanol_context_not_confirmed/
);


const methanolAg =
  ClinicalTools
    .calculateBrazilMethanolContext({
      explicit_methanol_context:
        true,
      sodium_mmol_l:
        140,
      potassium_mmol_l:
        4,
      chloride_mmol_l:
        104,
      bicarbonate_mmol_l:
        20
    });


assert.strictEqual(
  methanolAg
    .ministry_anion_gap_mmol_l,
  20
);

assert.strictEqual(
  methanolAg
    .ministry_anion_gap_potassium_included,
  true
);

assert.strictEqual(
  methanolAg
    .anion_gap_gt_12,
  true
);

assert.strictEqual(
  methanolAg
    .methanol_diagnosis_applied,
  false
);


const calculatedMethanolOsm =
  (
    5
    + 5
    + 1.86 * 140
  )
  / 0.93;


const methanolGap =
  ClinicalTools
    .calculateBrazilMethanolContext({
      explicit_methanol_context:
        true,
      sodium_mmol_l:
        140,
      potassium_mmol_l:
        null,
      chloride_mmol_l:
        null,
      bicarbonate_mmol_l:
        null,
      glucose_mmol_l:
        5,
      urea_mmol_l:
        5,
      measured_osmolality_mosm_kg:
        calculatedMethanolOsm + 14
    });


assert.strictEqual(
  methanolGap
    .osmolar_gap_mosm_kg,
  14
);

assert.strictEqual(
  methanolGap
    .osmolar_gap_gt_10,
  true
);

assert.strictEqual(
  methanolGap
    .osmolar_gap_gt_25,
  false
);

assert.strictEqual(
  methanolGap
    .ministry_osmolality_uses_urea_not_bun,
  true
);

assert.strictEqual(
  methanolGap
    .urea_bun_substitution_applied,
  false
);

assert.strictEqual(
  methanolGap
    .unit_domain_mixed,
  false
);


const methanolExact10 =
  ClinicalTools
    .calculateBrazilMethanolContext({
      explicit_methanol_context:
        true,
      sodium_mmol_l:
        140,
      potassium_mmol_l:
        null,
      chloride_mmol_l:
        null,
      bicarbonate_mmol_l:
        null,
      glucose_mmol_l:
        5,
      urea_mmol_l:
        5,
      measured_osmolality_mosm_kg:
        calculatedMethanolOsm + 10
    });


assert.strictEqual(
  methanolExact10
    .osmolar_gap_gt_10,
  false
);


const methanolExact25 =
  ClinicalTools
    .calculateBrazilMethanolContext({
      explicit_methanol_context:
        true,
      sodium_mmol_l:
        140,
      potassium_mmol_l:
        null,
      chloride_mmol_l:
        null,
      bicarbonate_mmol_l:
        null,
      glucose_mmol_l:
        5,
      urea_mmol_l:
        5,
      measured_osmolality_mosm_kg:
        calculatedMethanolOsm + 25
    });


assert.strictEqual(
  methanolExact25
    .osmolar_gap_gt_25,
  false
);


assert.throws(
  () =>
    ClinicalTools
      .calculateBrazilMethanolContext({
        explicit_methanol_context:
          true,
        sodium_mmol_l:
          140,
        potassium_mmol_l:
          null,
        chloride_mmol_l:
          null,
        bicarbonate_mmol_l:
          null,
        glucose_mmol_l:
          null,
        urea_mmol_l:
          null,
        measured_osmolality_mosm_kg:
          300
      }),

  /measured_osmolality_requires_methanol_osmolality_inputs/
);


console.log(
  'metabolic_i18n_qc: Brazil methanol context parity PASS'
);
