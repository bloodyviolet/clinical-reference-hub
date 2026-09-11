const fs =
  require('fs');

const vm =
  require('vm');

const assert =
  require('assert');


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


for (const name of [
  'calculateSteadiTug',
  'calculateSteadiChairStand30s',
  'calculateSteadiFourStageBalance',
  'calculateSteadiOrthostaticBp'
]) {
  assert.strictEqual(
    typeof ClinicalTools[name],
    'function',
    `${name} missing`
  );
}


function tug(
  overrides = {}
) {
  return (
    ClinicalTools
      .calculateSteadiTug({
        time_seconds:
          10,

        walking_aid_used:
          false,

        standard_3m_protocol_confirmed:
          true,

        ...overrides
      })
  );
}


function chair(
  overrides = {}
) {
  return (
    ClinicalTools
      .calculateSteadiChairStand30s({
        age_years:
          60,

        sex:
          'male',

        repetitions:
          14,

        arms_required_to_stand:
          false,

        standard_30_second_protocol_confirmed:
          true,

        ...overrides
      })
  );
}


function balance(
  overrides = {}
) {
  return (
    ClinicalTools
      .calculateSteadiFourStageBalance({
        side_by_side_seconds:
          10,

        semi_tandem_seconds:
          10,

        tandem_seconds:
          10,

        one_leg_seconds:
          10,

        assistive_device_used:
          false,

        standard_four_stage_protocol_confirmed:
          true,

        ...overrides
      })
  );
}


function ortho(
  overrides = {}
) {
  return (
    ClinicalTools
      .calculateSteadiOrthostaticBp({
        supine_sbp_mm_hg:
          130,

        supine_dbp_mm_hg:
          80,

        supine_pulse_bpm:
          70,

        standing_1m_sbp_mm_hg:
          125,

        standing_1m_dbp_mm_hg:
          77,

        standing_1m_pulse_bpm:
          76,

        standing_3m_sbp_mm_hg:
          125,

        standing_3m_dbp_mm_hg:
          77,

        standing_3m_pulse_bpm:
          74,

        lightheaded_or_dizzy:
          false,

        standard_5_1_3_protocol_confirmed:
          true,

        ...overrides
      })
  );
}


// ---------------------------------------------------------------
// TUG
// ---------------------------------------------------------------

assert.strictEqual(
  tug({
    time_seconds:
      11.99
  }).increased_fall_risk,
  false
);


assert.strictEqual(
  tug({
    time_seconds:
      12
  }).increased_fall_risk,
  true
);


const tugAid =
  tug({
    walking_aid_used:
      true
  });


assert.strictEqual(
  tugAid.walking_aid_allowed,
  true
);


assert.strictEqual(
  tugAid.walking_aid_used,
  true
);


assert.strictEqual(
  tugAid.course_distance_m,
  3
);


assert.strictEqual(
  tugAid.course_distance_ft,
  10
);


assert.strictEqual(
  tugAid.ivcf_four_meter_gait_inferred,
  false
);


assert.throws(
  () =>
    tug({
      standard_3m_protocol_confirmed:
        false
    })
);


assert.throws(
  () =>
    tug({
      time_seconds:
        0
    })
);


// ---------------------------------------------------------------
// Chair Stand
// ---------------------------------------------------------------

const chairTable = [
  [60, 'male', 14],
  [64, 'female', 12],
  [65, 'male', 12],
  [69, 'female', 11],
  [70, 'male', 12],
  [74, 'female', 10],
  [75, 'male', 11],
  [79, 'female', 10],
  [80, 'male', 10],
  [84, 'female', 9],
  [85, 'male', 8],
  [89, 'female', 8],
  [90, 'male', 7],
  [94, 'female', 4]
];


for (
  const [
    age,
    sex,
    threshold
  ]
  of chairTable
) {
  const below =
    chair({
      age_years:
        age,

      sex,

      repetitions:
        threshold - 1
    });


  const exact =
    chair({
      age_years:
        age,

      sex,

      repetitions:
        threshold
    });


  assert.strictEqual(
    below.below_average_threshold,
    threshold
  );


  assert.strictEqual(
    below.below_average,
    true
  );


  assert.strictEqual(
    below.increased_fall_risk,
    true
  );


  assert.strictEqual(
    exact.below_average,
    false
  );


  assert.strictEqual(
    exact.increased_fall_risk,
    false
  );
}


for (const age of [
  95,
  100,
  125
]) {
  const result =
    chair({
      age_years:
        age,

      sex:
        'female',

      repetitions:
        1
    });


  assert.strictEqual(
    result.reference_age_band,
    null
  );


  assert.strictEqual(
    result.below_average_threshold,
    null
  );


  assert.strictEqual(
    result.reference_classification_available,
    false
  );


  assert.strictEqual(
    result.below_average,
    null
  );


  assert.strictEqual(
    result.increased_fall_risk,
    null
  );


  assert.strictEqual(
    result.cutoff_extrapolated,
    false
  );
}


const armUse =
  chair({
    repetitions:
      9,

    arms_required_to_stand:
      true
  });


assert.strictEqual(
  armUse.observed_repetitions_input,
  9
);


assert.strictEqual(
  armUse.recorded_repetitions,
  0
);


assert.strictEqual(
  armUse.test_stopped_due_to_arm_use,
  true
);


assert.throws(
  () =>
    chair({
      age_years:
        59
    })
);


assert.throws(
  () =>
    chair({
      sex:
        'other'
    })
);


assert.throws(
  () =>
    chair({
      standard_30_second_protocol_confirmed:
        false
    })
);


// ---------------------------------------------------------------
// 4-Stage Balance
// ---------------------------------------------------------------

const fullBalance =
  balance();


assert.strictEqual(
  fullBalance.tandem_held_10_seconds,
  true
);


assert.strictEqual(
  fullBalance.increased_fall_risk,
  false
);


assert.strictEqual(
  fullBalance.last_stage_attempted,
  'one_leg'
);


const tandemNine =
  balance({
    tandem_seconds:
      9,

    one_leg_seconds:
      null
  });


assert.strictEqual(
  tandemNine.tandem_held_10_seconds,
  false
);


assert.strictEqual(
  tandemNine.increased_fall_risk,
  true
);


assert.strictEqual(
  tandemNine.last_stage_attempted,
  'tandem'
);


const sideFailure =
  balance({
    side_by_side_seconds:
      8,

    semi_tandem_seconds:
      null,

    tandem_seconds:
      null,

    one_leg_seconds:
      null
  });


assert.strictEqual(
  sideFailure.last_stage_attempted,
  'side_by_side'
);


assert.strictEqual(
  sideFailure.increased_fall_risk,
  true
);


assert.throws(
  () =>
    balance({
      side_by_side_seconds:
        8,

      semi_tandem_seconds:
        4,

      tandem_seconds:
        null,

      one_leg_seconds:
        null
    })
);


assert.throws(
  () =>
    balance({
      side_by_side_seconds:
        10,

      semi_tandem_seconds:
        null,

      tandem_seconds:
        null,

      one_leg_seconds:
        null
    })
);


const oneLegZero =
  balance({
    one_leg_seconds:
      0
  });


assert.strictEqual(
  oneLegZero.tandem_held_10_seconds,
  true
);


assert.strictEqual(
  oneLegZero.increased_fall_risk,
  false
);


assert.throws(
  () =>
    balance({
      assistive_device_used:
        true
    })
);


assert.throws(
  () =>
    balance({
      tandem_seconds:
        10.1
    })
);


assert.throws(
  () =>
    balance({
      standard_four_stage_protocol_confirmed:
        false
    })
);


// ---------------------------------------------------------------
// Orthostatic BP
// ---------------------------------------------------------------

const normal =
  ortho();


assert.strictEqual(
  normal.abnormal_steadi_orthostatic_assessment,
  false
);


assert.strictEqual(
  normal.systolic_threshold_met,
  false
);


assert.strictEqual(
  normal.diastolic_threshold_met,
  false
);


const exactSbp =
  ortho({
    standing_1m_sbp_mm_hg:
      110
  });


assert.strictEqual(
  exactSbp.systolic_drop_1m_mm_hg,
  20
);


assert.strictEqual(
  exactSbp.systolic_threshold_met,
  true
);


assert.strictEqual(
  exactSbp.abnormal_steadi_orthostatic_assessment,
  true
);


const exactDbp =
  ortho({
    standing_3m_dbp_mm_hg:
      70
  });


assert.strictEqual(
  exactDbp.diastolic_drop_3m_mm_hg,
  10
);


assert.strictEqual(
  exactDbp.diastolic_threshold_met,
  true
);


const symptomsOnly =
  ortho({
    lightheaded_or_dizzy:
      true
  });


assert.strictEqual(
  symptomsOnly.systolic_threshold_met,
  false
);


assert.strictEqual(
  symptomsOnly.diastolic_threshold_met,
  false
);


assert.strictEqual(
  symptomsOnly.abnormal_steadi_orthostatic_assessment,
  true
);


const laterDrop =
  ortho({
    standing_1m_sbp_mm_hg:
      125,

    standing_3m_sbp_mm_hg:
      105
  });


assert.strictEqual(
  laterDrop.systolic_drop_1m_mm_hg,
  5
);


assert.strictEqual(
  laterDrop.systolic_drop_3m_mm_hg,
  25
);


assert.strictEqual(
  laterDrop.maximum_systolic_drop_mm_hg,
  25
);


assert.throws(
  () =>
    ortho({
      standard_5_1_3_protocol_confirmed:
        false
    })
);


assert.throws(
  () =>
    ortho({
      standing_1m_sbp_mm_hg:
        60,

      standing_1m_dbp_mm_hg:
        70
    })
);


const pulseVariation =
  ortho({
    standing_1m_pulse_bpm:
      120,

    standing_3m_pulse_bpm:
      50
  });


assert.strictEqual(
  Object.hasOwn(
    pulseVariation,
    'pulse_threshold'
  ),
  false
);


// ---------------------------------------------------------------
// Instrument-separation contract
// ---------------------------------------------------------------

for (const result of [
  tug(),
  chair(),
  balance(),
  ortho()
]) {
  assert.strictEqual(
    result.source_role,
    'complementary_international_guidance'
  );


  assert.strictEqual(
    result.national_sus_threshold_applied,
    false
  );


  assert.strictEqual(
    result.automatic_cross_instrument_inference_applied,
    false
  );


  assert.strictEqual(
    result.synthetic_cross_instrument_score_applied,
    false
  );
}


assert.strictEqual(
  ortho().fall_risk_classification_applied,
  false
);


console.log(
  'steadi_i18n_qc: TUG/Chair/Balance/Orthostatic browser parity PASS'
);
