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


const sourceContract =
  JSON.parse(
    fs.readFileSync(
      'data/clinical-sources/four_gcsp.json',
      'utf8'
    )
  );


vm.runInThisContext(
  toolsSource,
  {
    filename:
      'assets/clinical-tools.js'
  }
);


assert.strictEqual(
  typeof ClinicalTools.calculateGcs,
  'function'
);

assert.strictEqual(
  typeof ClinicalTools.calculateGcsp,
  'function'
);

assert.strictEqual(
  typeof ClinicalTools.calculateFour,
  'function'
);


for (
  const vector
  of sourceContract.reference_vectors.gcs
) {
  const result =
    ClinicalTools.calculateGcs({
      eye:
        vector.eye,

      verbal:
        vector.verbal,

      motor:
        vector.motor
    });

  assert.strictEqual(
    result.total,
    vector.expected_total,
    vector.id
  );

  assert.deepStrictEqual(
    result.components,
    {
      eye:
        vector.eye,

      verbal:
        vector.verbal,

      motor:
        vector.motor
    }
  );
}


for (
  const vector
  of sourceContract.reference_vectors.four
) {
  const result =
    ClinicalTools.calculateFour({
      eye:
        vector.eye,

      motor:
        vector.motor,

      brainstem:
        vector.brainstem,

      respiration:
        vector.respiration
    });

  assert.strictEqual(
    result.total,
    vector.expected_total,
    vector.id
  );
}


function gcsForTotal(
  total
) {
  for (
    let eye = 1;
    eye <= 4;
    eye += 1
  ) {
    for (
      let verbal = 1;
      verbal <= 5;
      verbal += 1
    ) {
      for (
        let motor = 1;
        motor <= 6;
        motor += 1
      ) {
        if (
          eye
          + verbal
          + motor
          === total
        ) {
          return {
            eye,
            verbal,
            motor
          };
        }
      }
    }
  }

  throw new Error(
    `No GCS decomposition for ${total}`
  );
}


for (
  const vector
  of sourceContract.reference_vectors.gcsp
) {
  let gcs;

  if (
    vector.gcs_total === null
  ) {
    gcs = {
      eye:
        4,

      verbal:
        'NT',

      motor:
        6
    };

  } else {
    gcs =
      gcsForTotal(
        vector.gcs_total
      );
  }

  const result =
    ClinicalTools.calculateGcsp({
      ...gcs,

      unreactive_pupils:
        vector.prs
    });

  assert.strictEqual(
    result.total,
    vector.expected,
    vector.id
  );

  assert.strictEqual(
    result.gcs_total,
    vector.gcs_total,
    vector.id
  );
}


const ntGcs =
  ClinicalTools.calculateGcs({
    eye:
      4,

    verbal:
      'NT',

    motor:
      6
  });

assert.strictEqual(
  ntGcs.evaluable,
  false
);

assert.strictEqual(
  ntGcs.total,
  null
);

assert.deepStrictEqual(
  ntGcs.nt_components,
  [
    'verbal'
  ]
);


const unknownPupils =
  ClinicalTools.calculateGcsp({
    eye:
      4,

    verbal:
      5,

    motor:
      6,

    unreactive_pupils:
      null
  });

assert.strictEqual(
  unknownPupils.evaluable,
  false
);

assert.strictEqual(
  unknownPupils.total,
  null
);

assert.deepStrictEqual(
  unknownPupils.incomplete_reasons,
  [
    'pupil_reactivity_unknown'
  ]
);


const bothIncomplete =
  ClinicalTools.calculateGcsp({
    eye:
      'NT',

    verbal:
      5,

    motor:
      6,

    unreactive_pupils:
      null
  });

assert.strictEqual(
  bothIncomplete.total,
  null
);

assert.deepStrictEqual(
  bothIncomplete.incomplete_reasons,
  [
    'gcs_not_numeric',
    'pupil_reactivity_unknown'
  ]
);


const incompleteFour =
  ClinicalTools.calculateFour({
    eye:
      4,

    motor:
      4,

    brainstem:
      null,

    respiration:
      4
  });

assert.strictEqual(
  incompleteFour.evaluable,
  false
);

assert.strictEqual(
  incompleteFour.total,
  null
);

assert.deepStrictEqual(
  incompleteFour.missing_domains,
  [
    'brainstem'
  ]
);


for (
  const value
  of [
    true,
    false,
    0,
    5,
    2.5,
    '4'
  ]
) {
  assert.throws(
    () =>
      ClinicalTools.calculateGcs({
        eye:
          value,

        verbal:
          5,

        motor:
          6
      })
  );
}


for (
  const value
  of [
    true,
    false,
    -1,
    3,
    1.5,
    '1'
  ]
) {
  assert.throws(
    () =>
      ClinicalTools.calculateGcsp({
        eye:
          4,

        verbal:
          5,

        motor:
          6,

        unreactive_pupils:
          value
      })
  );
}


for (
  const value
  of [
    true,
    false,
    -1,
    5,
    2.5,
    '2'
  ]
) {
  assert.throws(
    () =>
      ClinicalTools.calculateFour({
        eye:
          value,

        motor:
          4,

        brainstem:
          4,

        respiration:
          4
      })
  );
}


// A client-derived value may be present as an irrelevant extra,
// but it cannot override the raw observations.
const antiTamper =
  ClinicalTools.calculateGcsp({
    eye:
      4,

    verbal:
      5,

    motor:
      6,

    unreactive_pupils:
      2,

    gcs_total:
      3,

    gcs_result: {
      total:
        3
    }
  });

assert.strictEqual(
  antiTamper.gcs_total,
  15
);

assert.strictEqual(
  antiTamper.total,
  13
);


assert.strictEqual(
  Object.hasOwn(
    antiTamper,
    'mortality'
  ),
  false
);

assert.strictEqual(
  Object.hasOwn(
    incompleteFour,
    'prognosis'
  ),
  false
);


console.log(
  'four_gcsp_offline_qc: '
  + 'GCS/GCS-P/FOUR source vectors, '
  + 'strict input firewalls and '
  + 'anti-tampering PASS'
);
