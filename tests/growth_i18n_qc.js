const fs = require('fs');
const vm = require('vm');
const assert = require('assert');


const source =
  fs.readFileSync(
    'assets/growth-tools.js',
    'utf8'
  );


const vectors =
  JSON.parse(
    fs.readFileSync(
      'tests/fixtures/growth_vectors.json',
      'utf8'
    )
  );


let fetchCount = 0;


global.caches =
  undefined;


global.fetch =
  async function fetchReference(
    url
  ) {
    fetchCount += 1;

    const path =
      String(url)
        .replace(
          /^\/+/,
          ''
        );


    const local =
      fs.readFileSync(
        path,
        'utf8'
      );


    return {
      ok: true,

      async json() {
        return JSON.parse(
          local
        );
      }
    };
  };


vm.runInThisContext(
  source,
  {
    filename:
      'assets/growth-tools.js'
  }
);


assert.strictEqual(
  typeof ClinicalGrowthTools
    .calculateWhoGrowth,
  'function'
);


function codeOf(
  value
) {
  return value
    ? value.code
    : null;
}


function compareIndicator(
  name,
  actual,
  expected
) {
  if (expected === null) {
    assert.strictEqual(
      actual,
      null,
      `${name}: expected null`
    );

    return;
  }


  assert(
    actual,
    `${name}: missing actual indicator`
  );


  assert.strictEqual(
    actual.z_score,
    expected.z_score,
    `${name}: z-score`
  );


  assert.strictEqual(
    actual.percentile_available,
    expected.percentile_available,
    `${name}: percentile availability`
  );


  if (
    expected.percentile === null
  ) {
    assert.strictEqual(
      actual.percentile,
      null,
      `${name}: percentile`
    );

  } else {
    assert(
      Math.abs(
        actual.percentile
        - expected.percentile
      ) <= 0.01,
      (
        `${name}: percentile `
        + `${actual.percentile} != `
        + `${expected.percentile}`
      )
    );
  }


  assert.strictEqual(
    actual.reference_standard,
    expected.reference_standard,
    `${name}: reference standard`
  );


  assert.strictEqual(
    actual.reference_table,
    expected.reference_table,
    `${name}: reference table`
  );


  assert.strictEqual(
    codeOf(
      actual.classification_who
    ),
    codeOf(
      expected.classification_who
    ),
    `${name}: WHO classification`
  );


  assert.strictEqual(
    codeOf(
      actual.classification_br
    ),
    codeOf(
      expected.classification_br
    ),
    `${name}: Brazil classification`
  );


  assert.strictEqual(
    actual.plausibility_flag,
    expected.plausibility_flag,
    `${name}: plausibility`
  );


  assert.strictEqual(
    actual.who_plausibility_range,
    expected.who_plausibility_range,
    `${name}: plausibility range`
  );


  if (
    Object.hasOwn(
      expected,
      'brazil_routine_monitoring_applicable'
    )
  ) {
    assert.strictEqual(
      actual
        .brazil_routine_monitoring_applicable,
      expected
        .brazil_routine_monitoring_applicable,
      `${name}: Brazil HC monitoring`
    );
  }
}


(async () => {
  for (const vector of vectors) {
    const actual =
      await ClinicalGrowthTools
        .calculateWhoGrowth(
          vector.input
        );


    const expected =
      vector.expected;


    assert.strictEqual(
      actual.tool,
      expected.tool,
      `${vector.name}: tool`
    );


    assert.strictEqual(
      actual.sex,
      expected.sex,
      `${vector.name}: sex`
    );


    assert.strictEqual(
      actual.age_basis,
      expected.age_basis,
      `${vector.name}: age basis`
    );


    assert.strictEqual(
      actual.who_age_days,
      expected.who_age_days,
      `${vector.name}: age days`
    );


    assert.strictEqual(
      actual.who_age_months,
      expected.who_age_months,
      `${vector.name}: age months`
    );


    assert.strictEqual(
      actual.measurement_adjustment_cm,
      expected.measurement_adjustment_cm,
      `${vector.name}: adjustment`
    );


    assert.strictEqual(
      actual.length_height_effective_cm,
      expected.length_height_effective_cm,
      `${vector.name}: effective size`
    );


    assert.strictEqual(
      actual.bmi_kg_m2,
      expected.bmi_kg_m2,
      `${vector.name}: BMI`
    );


    for (const indicator of [
      'weight_for_age',
      'length_height_for_age',
      'weight_for_length_height',
      'bmi_for_age',
      'head_circumference_for_age'
    ]) {
      compareIndicator(
        `${vector.name}/${indicator}`,
        actual.indicators[indicator],
        expected.indicators[indicator]
      );
    }


    assert.deepStrictEqual(
      actual.warnings_pt,
      expected.warnings_pt,
      `${vector.name}: PT warnings`
    );


    assert.deepStrictEqual(
      actual.warnings_en,
      expected.warnings_en,
      `${vector.name}: EN warnings`
    );


    assert.deepStrictEqual(
      actual.provenance,
      expected.provenance,
      `${vector.name}: provenance`
    );
  }


  // The bundle must be cached in-memory after the first calculation.
  assert.strictEqual(
    fetchCount,
    10,
    'growth reference bundle should load exactly once'
  );


  // Direct official WHO vectors, independent of generated fixture labels.
  const under5 =
    await ClinicalGrowthTools
      .calculateWhoGrowth({
        sex: 'male',
        age_value: 1001,
        age_unit: 'days',
        weight_kg: 18,
        length_height_cm: 120,
        measurement_position: 'height'
      });


  assert.strictEqual(
    under5
      .indicators
      .length_height_for_age
      .z_score,
    7.31
  );


  assert.strictEqual(
    under5
      .indicators
      .weight_for_age
      .z_score,
    2.20
  );


  assert.strictEqual(
    under5
      .indicators
      .weight_for_length_height
      .z_score,
    -2.39
  );


  assert.strictEqual(
    under5
      .indicators
      .bmi_for_age
      .z_score,
    -3.01
  );


  const older =
    await ClinicalGrowthTools
      .calculateWhoGrowth({
        sex: 'male',
        age_value: 100,
        age_unit: 'months',
        weight_kg: 30,
        length_height_cm: 100,
        measurement_position: 'height'
      });


  assert.strictEqual(
    older
      .indicators
      .length_height_for_age
      .z_score,
    -5.04
  );


  assert.strictEqual(
    older
      .indicators
      .weight_for_age
      .z_score,
    0.87
  );


  assert.strictEqual(
    older
      .indicators
      .bmi_for_age
      .z_score,
    5.03
  );


  assert.strictEqual(
    older
      .indicators
      .bmi_for_age
      .classification_who
      .code,
    'obesity'
  );


  assert.strictEqual(
    older
      .indicators
      .bmi_for_age
      .classification_br
      .code,
    'severe_obesity'
  );


  await assert.rejects(
    ClinicalGrowthTools
      .calculateWhoGrowth({
        sex: 'male',
        age_value: 12,
        age_unit: 'months'
      }),

    /anthropometric_measurement_required/
  );


  await assert.rejects(
    ClinicalGrowthTools
      .calculateWhoGrowth({
        sex: 'female',
        age_value: 100,
        age_unit: 'months',
        length_height_cm: 140,
        measurement_position: 'length'
      }),

    /who2007_requires_standing_height/
  );


  console.log(
    'growth_i18n_qc: WHO/SISVAN Python-browser-offline parity PASS'
  );

})().catch(
  error => {
    console.error(error);
    process.exit(1);
  }
);
