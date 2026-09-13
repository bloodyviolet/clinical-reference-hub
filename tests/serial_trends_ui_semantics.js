'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT =
  path.resolve(__dirname, '..');

const runtime =
  require(
    path.join(
      ROOT,
      'assets',
      'serial-trends-runtime.js'
    )
  );

const registry =
  JSON.parse(
    fs.readFileSync(
      path.join(
        ROOT,
        'assets',
        'serial-trends-instrument-registry.json'
      ),
      'utf8'
    )
  );

assert.strictEqual(
  registry.instruments.length,
  18
);

assert.strictEqual(
  registry.global_contract
    .all_series_ephemeral,
  true
);

assert.strictEqual(
  registry.global_contract
    .numeric_auto_discovery,
  false
);

assert.strictEqual(
  registry.global_contract
    .connect_points,
  false
);

assert.strictEqual(
  registry.global_contract
    .interpolation,
  false
);

assert.strictEqual(
  registry.global_contract
    .smoothing,
  false
);

assert.strictEqual(
  registry.global_contract
    .regression,
  false
);

assert.strictEqual(
  registry.global_contract
    .forecasting,
  false
);

assert.strictEqual(
  registry.global_contract
    .automatic_direction_interpretation,
  false
);

const store =
  runtime.createStore(
    registry,
    {
      nowProvider: () =>
        new Date(
          '2026-09-13T15:00:00.000Z'
        )
    }
  );

const requestOne = {
  eye: 4,
  verbal: 'NT',
  motor: 6
};

const resultOne = {
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
    'verbal_not_testable'
};

const observationOne =
  store.addObservation({
    instrumentKey: 'gcs',
    observedAt:
      '2026-09-13T10:00:00-03:00',
    requestSnapshot:
      requestOne,
    resultSnapshot:
      resultOne,
    executionSource:
      'api'
  });

requestOne.eye = 1;
resultOne.components.eye = 1;

assert.strictEqual(
  observationOne
    .request_snapshot
    .eye,
  4
);

assert.strictEqual(
  observationOne
    .result_snapshot
    .components
    .eye,
  4
);

assert(
  Object.isFrozen(
    observationOne.request_snapshot
  )
);

assert(
  Object.isFrozen(
    observationOne.result_snapshot
  )
);

const modelOne =
  store.displayModel(
    observationOne
  );

assert.strictEqual(
  modelOne.execution_source,
  'api'
);

const verbal =
  modelOne
    .component_fields
    .find(
      (field) =>
        field.path
        === 'components.verbal'
    );

assert(verbal);

assert.strictEqual(
  verbal.value,
  'NT'
);

const gcsPlot =
  modelOne
    .plot_groups
    .find(
      (group) =>
        group.group_id
        === 'gcs_total'
    );

assert(gcsPlot);

assert.strictEqual(
  gcsPlot.connect_points,
  false
);

assert.strictEqual(
  gcsPlot
    .fields[0]
    .plot_value,
  null
);

assert.strictEqual(
  gcsPlot
    .fields[0]
    .gap,
  true
);

const observationTwo =
  store.addObservation({
    instrumentKey: 'gcs',
    observedAt:
      '2026-09-13T13:00:00Z',
    requestSnapshot: {
      eye: 4,
      verbal: 5,
      motor: 6
    },
    resultSnapshot: {
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

assert.strictEqual(
  observationOne
    .observed_at_epoch_ms,
  observationTwo
    .observed_at_epoch_ms
);

const groups =
  store.chronologyGroups(
    'gcs'
  );

assert.strictEqual(
  groups.length,
  1
);

assert.strictEqual(
  groups[0].equal_time_tie,
  true
);

assert.strictEqual(
  groups[0].clinical_order,
  null
);

assert.strictEqual(
  groups[0].observations.length,
  2
);

assert.strictEqual(
  groups[0]
    .observations[0]
    .observed_at,
  '2026-09-13T10:00:00-03:00'
);

assert.strictEqual(
  groups[0]
    .observations[1]
    .observed_at,
  '2026-09-13T13:00:00Z'
);

const modelTwo =
  store.displayModel(
    observationTwo
  );

const numericPlot =
  modelTwo
    .plot_groups
    .find(
      (group) =>
        group.group_id
        === 'gcs_total'
    );

assert.strictEqual(
  numericPlot
    .fields[0]
    .plot_value,
  15
);

assert.strictEqual(
  numericPlot
    .fields[0]
    .gap,
  false
);

assert.strictEqual(
  modelTwo.execution_source,
  'offline'
);

const caderneta =
  store.addObservation({
    instrumentKey:
      'brazil_caderneta_falls',
    observedAt:
      '2026-09-13T14:00:00Z',
    requestSnapshot: {
      concern_about_falling:
        true
    },
    resultSnapshot: {
      positive_items_count: 1,
      positive_items: [
        'concern_about_falling'
      ],
      assessment_indicated: true,
      any_yes_rule_applied: true,
      weighted_score_applied: false,
      foreign_weighted_score_imported:
        false,
      interpretation_pt:
        'context',
      interpretation_en:
        'context'
    },
    executionSource:
      'api'
  });

const cadernetaModel =
  store.displayModel(
    caderneta
  );

assert.deepStrictEqual(
  cadernetaModel.plot_groups,
  []
);

assert.throws(
  () =>
    store.addObservation({
      instrumentKey:
        'gcs',
      observedAt:
        '2026-09-13T16:00:00Z',
      requestSnapshot: {},
      resultSnapshot: {},
      executionSource:
        'api'
    }),
  /future_observed_at/
);

assert.throws(
  () =>
    store.addObservation({
      instrumentKey:
        'gcs',
      observedAt:
        '2026-09-13T14:00:00Z',
      requestSnapshot: {},
      resultSnapshot: {},
      executionSource:
        'cache'
    }),
  /invalid_execution_source/
);

store.clearInstrument(
  'gcs'
);

assert.strictEqual(
  store
    .chronologyGroups(
      'gcs'
    )
    .length,
  0
);

assert.strictEqual(
  store
    .chronologyGroups(
      'brazil_caderneta_falls'
    )
    .length,
  1
);

store.clearAll();

assert.strictEqual(
  store
    .chronologyGroups(
      'brazil_caderneta_falls'
    )
    .length,
  0
);

console.log(
  'serial_trends_ui_semantics: '
  + 'ties, NT/null gaps, immutable snapshots, '
  + 'registry-only plotting and clear isolation PASS'
);
