'use strict';

const assert =
  require('assert');

const fs =
  require('fs');

const path =
  require('path');


const repo =
  process.cwd();

const runtimePath =
  process.argv[2];

const contractPath =
  process.argv[3];


const Runtime =
  require(runtimePath);

const registry =
  JSON.parse(
    fs.readFileSync(
      path.join(
        repo,
        'data',
        'clinical-sources',
        'serial_trends_instrument_registry.json'
      ),
      'utf8'
    )
  );

const contract =
  JSON.parse(
    fs.readFileSync(
      contractPath,
      'utf8'
    )
  );


assert.strictEqual(
  registry.instruments.length,
  18
);

assert.strictEqual(
  contract.persistence
    .memory_only,
  true
);


function mustThrow(
  fn,
  code
) {
  assert.throws(
    fn,
    (error) =>
      (
        error
        instanceof Error
        && error.message === code
      )
  );
}


Runtime.parseObservedAt(
  '2026-09-13T03:00:00Z'
);

Runtime.parseObservedAt(
  '2026-09-13T00:00:00-03:00'
);

Runtime.parseObservedAt(
  '2026-09-13T03:00:00.123456789Z'
);


mustThrow(
  () =>
    Runtime.parseObservedAt(
      '2026-09-13T03:00:00'
    ),
  'observed_at_must_be_offset_aware_rfc3339'
);

mustThrow(
  () =>
    Runtime.parseObservedAt(
      '2026-09-13'
    ),
  'observed_at_must_be_offset_aware_rfc3339'
);

mustThrow(
  () =>
    Runtime.parseObservedAt(
      '2026-02-30T03:00:00Z'
    ),
  'invalid_observed_at_calendar_value'
);

mustThrow(
  () =>
    Runtime.parseObservedAt(
      '2026-13-01T03:00:00Z'
    ),
  'invalid_observed_at_calendar_value'
);


const originalRequest = {
  eye: 4,
  verbal: 'NT',
  motor: 6,
  nested: {
    example: true
  }
};

const originalResult = {
  tool: 'gcs',
  evaluable: false,
  total: null,
  components: {
    eye: 4,
    verbal: 'NT',
    motor: 6
  },
  nt_components: [
    'verbal'
  ],
  incomplete_reason:
    'not_testable_component'
};


const fixedNow =
  () =>
    new Date(
      '2026-09-13T13:30:00.000Z'
    );


const store =
  Runtime.createStore(
    registry,
    {
      nowProvider:
        fixedNow
    }
  );


const first =
  store.addObservation({
    instrumentKey:
      'gcs',
    observedAt:
      '2026-09-13T09:00:00-03:00',
    requestSnapshot:
      originalRequest,
    resultSnapshot:
      originalResult,
    executionSource:
      'api'
  });


assert.strictEqual(
  first.instrument_key,
  'gcs'
);

assert.strictEqual(
  first.observed_at,
  '2026-09-13T09:00:00-03:00'
);

assert.strictEqual(
  first.captured_at,
  '2026-09-13T13:30:00.000Z'
);

assert.strictEqual(
  first.execution_source,
  'api'
);

assert.strictEqual(
  first.result_snapshot
    .components
    .verbal,
  'NT'
);

assert.strictEqual(
  first.result_snapshot.total,
  null
);


originalRequest.eye = 1;
originalRequest.nested.example =
  false;

originalResult.total = 3;
originalResult.components.verbal =
  1;


assert.strictEqual(
  first.request_snapshot.eye,
  4
);

assert.strictEqual(
  first.request_snapshot
    .nested
    .example,
  true
);

assert.strictEqual(
  first.result_snapshot.total,
  null
);

assert.strictEqual(
  first.result_snapshot
    .components
    .verbal,
  'NT'
);


assert.strictEqual(
  Object.isFrozen(
    first
  ),
  true
);

assert.strictEqual(
  Object.isFrozen(
    first.request_snapshot
  ),
  true
);

assert.strictEqual(
  Object.isFrozen(
    first.result_snapshot
      .components
  ),
  true
);


mustThrow(
  () =>
    store.addObservation({
      instrumentKey:
        'gcs',
      observedAt:
        '2026-09-13T14:00:00Z',
      requestSnapshot:
        {},
      resultSnapshot:
        {},
      executionSource:
        'api'
    }),
  'future_observed_at'
);


mustThrow(
  () =>
    store.addObservation({
      instrumentKey:
        'gcs',
      observedAt:
        '2026-09-13T12:00:00Z',
      requestSnapshot:
        {},
      resultSnapshot:
        {},
      executionSource:
        'server'
    }),
  'invalid_execution_source'
);


mustThrow(
  () =>
    store.addObservation({
      instrumentKey:
        'not_a_tool',
      observedAt:
        '2026-09-13T12:00:00Z',
      requestSnapshot:
        {},
      resultSnapshot:
        {},
      executionSource:
        'api'
    }),
  'unknown_instrument_key'
);


mustThrow(
  () =>
    Runtime.snapshotClinicalJson({
      bad: Infinity
    }),
  'non_finite_json_number'
);


const cyclic = {};
cyclic.self = cyclic;

mustThrow(
  () =>
    Runtime.snapshotClinicalJson(
      cyclic
    ),
  'cyclic_json_value'
);


store.addObservation({
  instrumentKey:
    'gcs',
  observedAt:
    '2026-09-13T10:00:00-03:00',
  requestSnapshot: {
    eye: 4,
    verbal: 5,
    motor: 6
  },
  resultSnapshot: {
    tool: 'gcs',
    evaluable: true,
    total: 15,
    components: {
      eye: 4,
      verbal: 5,
      motor: 6
    },
    nt_components: [],
    incomplete_reason: null
  },
  executionSource:
    'offline'
});


store.addObservation({
  instrumentKey:
    'gcs',
  observedAt:
    '2026-09-13T12:00:00Z',
  requestSnapshot: {
    eye: 3,
    verbal: 4,
    motor: 6
  },
  resultSnapshot: {
    tool: 'gcs',
    evaluable: true,
    total: 13,
    components: {
      eye: 3,
      verbal: 4,
      motor: 6
    },
    nt_components: [],
    incomplete_reason: null
  },
  executionSource:
    'api'
});


const chronology =
  store.chronologyGroups(
    'gcs'
  );


assert.strictEqual(
  chronology.length,
  2
);

assert.strictEqual(
  chronology[0]
    .observations
    .length,
  2
);

assert.strictEqual(
  chronology[0]
    .equal_time_tie,
  true
);

assert.strictEqual(
  chronology[0]
    .clinical_order,
  null
);

assert.strictEqual(
  chronology[0]
    .observed_at_epoch_ms,
  Date.parse(
    '2026-09-13T12:00:00Z'
  )
);

assert.strictEqual(
  chronology[1]
    .equal_time_tie,
  false
);

assert.strictEqual(
  chronology[1]
    .observed_at_epoch_ms,
  Date.parse(
    '2026-09-13T13:00:00Z'
  )
);


const firstDisplay =
  store.displayModel(first);


assert.strictEqual(
  firstDisplay.instrument_key,
  'gcs'
);

assert.strictEqual(
  firstDisplay.execution_source,
  'api'
);

assert.strictEqual(
  firstDisplay.component_fields
    .length,
  3
);

assert.strictEqual(
  firstDisplay.component_fields[
    1
  ].value,
  'NT'
);

assert.strictEqual(
  firstDisplay.plot_groups.length,
  1
);

assert.strictEqual(
  firstDisplay.plot_groups[
    0
  ].fields[
    0
  ].plot_value,
  null
);

assert.strictEqual(
  firstDisplay.plot_groups[
    0
  ].fields[
    0
  ].gap,
  true
);


const cadernetaStore =
  Runtime.createStore(
    registry,
    {
      nowProvider:
        fixedNow
    }
  );


const caderneta =
  cadernetaStore
    .addObservation({
      instrumentKey:
        'brazil_caderneta_falls',
      observedAt:
        '2026-09-13T09:00:00-03:00',
      requestSnapshot: {
        age_years: 75
      },
      resultSnapshot: {
        tool:
          'brazil_caderneta_falls',
        age_years: 75,
        positive_items_count: 8,
        positive_items: [
          'example'
        ],
        assessment_indicated:
          true,
        any_yes_rule_applied:
          true,
        weighted_score_applied:
          false,
        foreign_weighted_score_imported:
          false,
        interpretation_pt:
          'teste',
        interpretation_en:
          'test'
      },
      executionSource:
        'offline'
    });


const cadernetaDisplay =
  cadernetaStore
    .displayModel(
      caderneta
    );


assert.strictEqual(
  cadernetaDisplay
    .plot_groups
    .length,
  0
);


const otherInstrument =
  store.addObservation({
    instrumentKey:
      'four_score',
    observedAt:
      '2026-09-13T12:00:00Z',
    requestSnapshot: {
      eye: 4,
      motor: 4,
      brainstem: 4,
      respiration: 4
    },
    resultSnapshot: {
      tool: 'four_score',
      evaluable: true,
      total: 16,
      components: {
        eye: 4,
        motor: 4,
        brainstem: 4,
        respiration: 4
      },
      missing_domains: [],
      incomplete_reason: null
    },
    executionSource:
      'api'
  });


assert.strictEqual(
  store.chronologyGroups(
    'four_score'
  ).length,
  1
);

assert.strictEqual(
  store.chronologyGroups(
    'gcs'
  ).length,
  2
);

assert.notStrictEqual(
  otherInstrument
    .instrument_key,
  first.instrument_key
);


store.clearInstrument(
  'four_score'
);

assert.strictEqual(
  store.chronologyGroups(
    'four_score'
  ).length,
  0
);

assert.strictEqual(
  store.chronologyGroups(
    'gcs'
  ).length,
  2
);


store.clearAll();

assert.strictEqual(
  store.chronologyGroups(
    'gcs'
  ).length,
  0
);


const mutableRegistry =
  JSON.parse(
    JSON.stringify(
      registry
    )
  );


const tamperStore =
  Runtime.createStore(
    mutableRegistry,
    {
      nowProvider:
        fixedNow
    }
  );


const tamperObservation =
  tamperStore.addObservation({
    instrumentKey:
      'gcs',
    observedAt:
      '2026-09-13T12:00:00Z',
    requestSnapshot: {
      eye: 4,
      verbal: 5,
      motor: 6
    },
    resultSnapshot: {
      tool: 'gcs',
      evaluable: true,
      total: 15,
      components: {
        eye: 4,
        verbal: 5,
        motor: 6
      },
      nt_components: [],
      incomplete_reason: null
    },
    executionSource:
      'api'
  });


const mutableGcsRegistry =
  mutableRegistry
    .instruments
    .find(
      (instrument) =>
        instrument.key === 'gcs'
    );


assert.ok(
  mutableGcsRegistry
);


mutableGcsRegistry
  .component_fields = [];

mutableGcsRegistry
  .plot_groups = [];


const tamperDisplay =
  tamperStore.displayModel(
    tamperObservation
  );


assert.strictEqual(
  tamperDisplay
    .component_fields
    .length,
  3
);

assert.strictEqual(
  tamperDisplay
    .plot_groups
    .length,
  1
);


console.log(
  'serial_trends_registry_snapshot_qc: '
  + 'caller registry mutation cannot alter '
  + 'store authorization PASS'
);


console.log(
  'serial_trends_runtime_qc: '
  + 'RFC3339 time, immutable snapshots, '
  + 'tie groups, registry rendering and '
  + 'memory-only isolation PASS'
);
