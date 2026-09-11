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


assert.strictEqual(
  typeof ClinicalTools
    .calculateCadernetaFallsCheckup,
  'function'
);

assert.strictEqual(
  typeof ClinicalTools
    .calculateIvcf20,
  'function'
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


function falls(
  overrides = {}
) {
  const input = {
    age_years:
      60
  };

  for (const key of FALL_KEYS) {
    input[key] = false;
  }

  Object.assign(
    input,
    overrides
  );

  return ClinicalTools
    .calculateCadernetaFallsCheckup(
      input
    );
}


function ivcf(
  overrides = {}
) {
  const input = {
    age_years:
      60
  };

  for (const key of IVCF_KEYS) {
    input[key] = false;
  }

  Object.assign(
    input,
    overrides
  );

  return ClinicalTools
    .calculateIvcf20(
      input
    );
}


// -------------------------------------------------------------------------
// Caderneta 2026
// -------------------------------------------------------------------------

const none =
  falls();


assert.strictEqual(
  none.positive_items_count,
  0
);

assert.deepStrictEqual(
  none.positive_items,
  []
);

assert.strictEqual(
  none.assessment_indicated,
  false
);

assert.strictEqual(
  none.any_yes_rule_applied,
  true
);

assert.strictEqual(
  none.weighted_score_applied,
  false
);

assert.strictEqual(
  none.foreign_weighted_score_imported,
  false
);

assert.strictEqual(
  none.fall_risk_classification_applied,
  false
);

assert.strictEqual(
  none.automatic_ivcf_inference_applied,
  false
);

assert.strictEqual(
  none.synthetic_cross_instrument_score_applied,
  false
);


for (const key of FALL_KEYS) {
  const one =
    falls({
      [key]:
        true
    });

  assert.strictEqual(
    one.positive_items_count,
    1,
    key
  );

  assert.deepStrictEqual(
    one.positive_items,
    [
      key
    ],
    key
  );

  assert.strictEqual(
    one.assessment_indicated,
    true,
    key
  );
}


const allFalls =
  falls(
    Object.fromEntries(
      FALL_KEYS.map(
        key => [
          key,
          true
        ]
      )
    )
  );


assert.strictEqual(
  allFalls.positive_items_count,
  12
);

assert.strictEqual(
  allFalls.assessment_indicated,
  true
);

assert.strictEqual(
  allFalls.weighted_score_applied,
  false
);


assert.throws(
  () =>
    ClinicalTools
      .calculateCadernetaFallsCheckup({
        age_years:
          60,
        ...Object.fromEntries(
          FALL_KEYS
            .slice(
              0,
              -1
            )
            .map(
              key => [
                key,
                false
              ]
            )
        )
      }),

  /incomplete_caderneta_falls_assessment/
);


// -------------------------------------------------------------------------
// IVCF-20
// -------------------------------------------------------------------------

for (
  const [
    age,
    expected
  ]
  of [
    [60, 0],
    [74, 0],
    [75, 1],
    [84, 1],
    [85, 3],
    [125, 3]
  ]
) {
  const result =
    ivcf({
      age_years:
        age
    });

  assert.strictEqual(
    result
      .dimension_scores
      .age,
    expected,
    `age ${age}`
  );
}


assert.throws(
  () =>
    ivcf({
      age_years:
        59
    }),

  /age_years_must_be_60_or_greater/
);


const instrumental =
  ivcf({
    stopped_shopping_due_health:
      true,
    stopped_managing_money_due_health:
      true,
    stopped_housework_due_health:
      true
  });


assert.strictEqual(
  instrumental
    .dimension_scores
    .instrumental_adl,
  4
);

assert.strictEqual(
  instrumental.total_score,
  4
);


const cognition =
  ivcf({
    forgetfulness_noted_by_others:
      true,
    worsening_forgetfulness:
      true,
    forgetfulness_impairs_daily_activity:
      true
  });


assert.strictEqual(
  cognition
    .dimension_scores
    .cognition,
  4
);


const aerobic =
  ivcf({
    unintentional_weight_loss_criterion:
      true,
    bmi_lt_22:
      true,
    calf_circumference_lt_31_cm:
      true,
    gait_4m_gt_5_seconds:
      true
  });


assert.strictEqual(
  aerobic
    .dimension_scores
    .aerobic_muscular_capacity,
  2
);


const comorbidity =
  ivcf({
    five_or_more_chronic_conditions:
      true,
    five_or_more_daily_medications:
      true,
    hospitalized_last_six_months:
      true
  });


assert.strictEqual(
  comorbidity
    .dimension_scores
    .multiple_comorbidities,
  4
);


const score6 =
  ivcf({
    stopped_bathing_due_health:
      true
  });


assert.strictEqual(
  score6.total_score,
  6
);

assert.strictEqual(
  score6.classification_code,
  'low'
);

assert.strictEqual(
  score6.reapplication_months_minimum,
  12
);


const score7 =
  ivcf({
    stopped_bathing_due_health:
      true,
    self_rated_health_regular_or_poor:
      true
  });


assert.strictEqual(
  score7.total_score,
  7
);

assert.strictEqual(
  score7.classification_code,
  'moderate'
);

assert.strictEqual(
  score7.reapplication_months_minimum,
  6
);


const score14 =
  ivcf({
    stopped_bathing_due_health:
      true,
    stopped_shopping_due_health:
      true,
    depressed_or_hopeless_last_month:
      true,
    anhedonia_last_month:
      true
  });


assert.strictEqual(
  score14.total_score,
  14
);

assert.strictEqual(
  score14.classification_code,
  'moderate'
);


const score15 =
  ivcf({
    stopped_bathing_due_health:
      true,
    stopped_shopping_due_health:
      true,
    depressed_or_hopeless_last_month:
      true,
    anhedonia_last_month:
      true,
    self_rated_health_regular_or_poor:
      true
  });


assert.strictEqual(
  score15.total_score,
  15
);

assert.strictEqual(
  score15.classification_code,
  'high'
);


const maximum =
  ivcf({
    age_years:
      85,

    ...Object.fromEntries(
      IVCF_KEYS.map(
        key => [
          key,
          true
        ]
      )
    )
  });


assert.strictEqual(
  maximum.total_score,
  40
);

assert.strictEqual(
  maximum.classification_code,
  'high'
);

assert.strictEqual(
  maximum.reapplication_months_minimum,
  6
);


const gait =
  ivcf({
    gait_4m_gt_5_seconds:
      true,
    two_or_more_falls_last_year:
      true
  });


assert.strictEqual(
  gait.gait_4m_gt_5_seconds,
  true
);

assert.strictEqual(
  gait.gait_4m_is_tug,
  false
);

assert.strictEqual(
  gait.fall_risk_classification_applied,
  false
);

assert.strictEqual(
  gait.automatic_caderneta_inference_applied,
  false
);

assert.strictEqual(
  gait.synthetic_cross_instrument_score_applied,
  false
);

assert.strictEqual(
  gait.complete_assessment_required,
  true
);

assert.strictEqual(
  gait.reapply_after_sentinel_event,
  true
);


const incompleteIvcf = {
  age_years:
    60
};

for (const key of IVCF_KEYS) {
  incompleteIvcf[key] =
    false;
}

delete incompleteIvcf[
  'hearing_impairs_daily_activity'
];


assert.throws(
  () =>
    ClinicalTools
      .calculateIvcf20(
        incompleteIvcf
      ),

  /incomplete_ivcf20_assessment/
);


console.log(
  'falls_function_i18n_qc: Caderneta 2026 + IVCF-20 browser parity PASS'
);
