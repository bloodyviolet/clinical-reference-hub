(() => {
  'use strict';


  const RFC3339_OFFSET_RE =
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})$/;


  function fail(code) {
    throw new Error(code);
  }


  function isPlainObject(value) {
    if (
      value === null
      || typeof value !== 'object'
    ) {
      return false;
    }

    const prototype =
      Object.getPrototypeOf(value);

    return (
      prototype === Object.prototype
      || prototype === null
    );
  }


  function assertClinicalJson(
    value,
    seen = new Set()
  ) {
    if (
      value === null
      || typeof value === 'string'
      || typeof value === 'boolean'
    ) {
      return;
    }

    if (typeof value === 'number') {
      if (!Number.isFinite(value)) {
        fail('non_finite_json_number');
      }

      return;
    }

    if (
      typeof value === 'undefined'
      || typeof value === 'function'
      || typeof value === 'symbol'
      || typeof value === 'bigint'
    ) {
      fail('non_json_value');
    }

    if (
      typeof value !== 'object'
    ) {
      fail('non_json_value');
    }

    if (seen.has(value)) {
      fail('cyclic_json_value');
    }

    seen.add(value);

    if (Array.isArray(value)) {
      for (const item of value) {
        assertClinicalJson(
          item,
          seen
        );
      }

      seen.delete(value);
      return;
    }

    if (!isPlainObject(value)) {
      fail('non_plain_json_object');
    }

    for (
      const [
        key,
        item
      ] of Object.entries(value)
    ) {
      if (typeof key !== 'string') {
        fail('invalid_json_key');
      }

      assertClinicalJson(
        item,
        seen
      );
    }

    seen.delete(value);
  }


  function deepFreeze(value) {
    if (
      value === null
      || typeof value !== 'object'
      || Object.isFrozen(value)
    ) {
      return value;
    }

    Object.freeze(value);

    for (
      const child
      of Object.values(value)
    ) {
      deepFreeze(child);
    }

    return value;
  }


  function snapshotClinicalJson(value) {
    assertClinicalJson(value);

    const clone =
      JSON.parse(
        JSON.stringify(value)
      );

    return deepFreeze(clone);
  }


  function daysInMonth(
    year,
    month
  ) {
    return new Date(
      Date.UTC(
        year,
        month,
        0
      )
    ).getUTCDate();
  }


  function parseObservedAt(value) {
    if (typeof value !== 'string') {
      fail('observed_at_must_be_string');
    }

    const match =
      RFC3339_OFFSET_RE.exec(value);

    if (!match) {
      fail('observed_at_must_be_offset_aware_rfc3339');
    }

    const year = Number(match[1]);
    const month = Number(match[2]);
    const day = Number(match[3]);
    const hour = Number(match[4]);
    const minute = Number(match[5]);
    const second = Number(match[6]);

    if (
      month < 1
      || month > 12
      || day < 1
      || day > daysInMonth(
        year,
        month
      )
      || hour > 23
      || minute > 59
      || second > 59
    ) {
      fail('invalid_observed_at_calendar_value');
    }

    const offset = match[8];

    if (offset !== 'Z') {
      const offsetHour =
        Number(
          offset.slice(
            1,
            3
          )
        );

      const offsetMinute =
        Number(
          offset.slice(
            4,
            6
          )
        );

      if (
        offsetHour > 23
        || offsetMinute > 59
      ) {
        fail('invalid_observed_at_offset');
      }
    }

    const epochMs =
      Date.parse(value);

    if (!Number.isFinite(epochMs)) {
      fail('invalid_observed_at');
    }

    return deepFreeze({
      raw: value,
      epoch_ms: epochMs
    });
  }


  function normaliseNow(nowProvider) {
    const value =
      nowProvider();

    if (
      !(value instanceof Date)
      || !Number.isFinite(
        value.getTime()
      )
    ) {
      fail('invalid_browser_clock');
    }

    return new Date(
      value.getTime()
    );
  }


  function registryMap(registry) {
    assertClinicalJson(registry);

    if (
      !registry
      || !Array.isArray(
        registry.instruments
      )
    ) {
      fail('invalid_registry');
    }

    const map =
      new Map();

    for (
      const instrument
      of registry.instruments
    ) {
      if (
        !instrument
        || typeof instrument.key !== 'string'
        || !instrument.key
        || instrument.table_enabled !== true
      ) {
        fail('invalid_registry_instrument');
      }

      if (map.has(instrument.key)) {
        fail('duplicate_registry_key');
      }

      map.set(
        instrument.key,
        instrument
      );
    }

    if (map.size !== 18) {
      fail('unexpected_registry_instrument_count');
    }

    return map;
  }


  function readPath(
    root,
    path
  ) {
    if (
      typeof path !== 'string'
      || !path
      || path.includes('*')
    ) {
      fail('invalid_registry_path');
    }

    const parts =
      path.split('.');

    let current =
      root;

    for (
      const part
      of parts
    ) {
      if (
        current === null
        || typeof current !== 'object'
        || !Object.prototype.hasOwnProperty.call(
          current,
          part
        )
      ) {
        return deepFreeze({
          present: false,
          value: null
        });
      }

      current =
        current[part];
    }

    return deepFreeze({
      present: true,
      value: current
    });
  }


  function sourceSnapshot(
    observation,
    source
  ) {
    if (source === 'request') {
      return observation
        .request_snapshot;
    }

    if (source === 'response') {
      return observation
        .result_snapshot;
    }

    fail('invalid_registry_field_source');
  }


  function extractRegisteredField(
    observation,
    field
  ) {
    if (
      !field
      || (
        field.source !== 'request'
        && field.source !== 'response'
      )
      || typeof field.path !== 'string'
    ) {
      fail('invalid_registry_field');
    }

    const extracted =
      readPath(
        sourceSnapshot(
          observation,
          field.source
        ),
        field.path
      );

    return deepFreeze({
      source: field.source,
      path: field.path,
      present: extracted.present,
      value: extracted.value
    });
  }


  function createObservation({
    instrumentKey,
    observedAt,
    requestSnapshot,
    resultSnapshot,
    executionSource,
    registryByKey,
    nowProvider,
    runtimeKey
  }) {
    if (
      typeof instrumentKey !== 'string'
      || !registryByKey.has(
        instrumentKey
      )
    ) {
      fail('unknown_instrument_key');
    }

    if (
      executionSource !== 'api'
      && executionSource !== 'offline'
    ) {
      fail('invalid_execution_source');
    }

    if (
      !Number.isSafeInteger(
        runtimeKey
      )
      || runtimeKey < 1
    ) {
      fail('invalid_runtime_key');
    }

    const observed =
      parseObservedAt(
        observedAt
      );

    const capturedDate =
      normaliseNow(
        nowProvider
      );

    const capturedEpoch =
      capturedDate.getTime();

    if (
      observed.epoch_ms
      > capturedEpoch
    ) {
      fail('future_observed_at');
    }

    const request =
      snapshotClinicalJson(
        requestSnapshot
      );

    const result =
      snapshotClinicalJson(
        resultSnapshot
      );

    return deepFreeze({
      runtime_key: runtimeKey,
      instrument_key: instrumentKey,
      observed_at: observed.raw,
      observed_at_epoch_ms:
        observed.epoch_ms,
      captured_at:
        capturedDate.toISOString(),
      request_snapshot: request,
      result_snapshot: result,
      execution_source:
        executionSource
    });
  }


  function createStore(
    registry,
    {
      nowProvider =
        () => new Date()
    } = {}
  ) {
    const registrySnapshot =
      snapshotClinicalJson(
        registry
      );

    const registryByKey =
      registryMap(
        registrySnapshot
      );

    const series =
      new Map();

    let nextRuntimeKey =
      1;


    function addObservation({
      instrumentKey,
      observedAt,
      requestSnapshot,
      resultSnapshot,
      executionSource
    }) {
      const observation =
        createObservation({
          instrumentKey,
          observedAt,
          requestSnapshot,
          resultSnapshot,
          executionSource,
          registryByKey,
          nowProvider,
          runtimeKey:
            nextRuntimeKey
        });

      nextRuntimeKey += 1;

      const current =
        series.get(
          instrumentKey
        )
        || [];

      current.push(
        observation
      );

      series.set(
        instrumentKey,
        current
      );

      return observation;
    }


    function rawSeries(
      instrumentKey
    ) {
      if (
        !registryByKey.has(
          instrumentKey
        )
      ) {
        fail('unknown_instrument_key');
      }

      return (
        series.get(
          instrumentKey
        )
        || []
      );
    }


    function chronologyGroups(
      instrumentKey
    ) {
      const observations =
        [...rawSeries(
          instrumentKey
        )];

      observations.sort(
        (
          left,
          right
        ) =>
          (
            left.observed_at_epoch_ms
            - right.observed_at_epoch_ms
          )
          || (
            left.runtime_key
            - right.runtime_key
          )
      );

      const groups = [];

      for (
        const observation
        of observations
      ) {
        let group =
          groups[
            groups.length - 1
          ];

        if (
          !group
          || group.observed_at_epoch_ms
            !== observation
              .observed_at_epoch_ms
        ) {
          group = {
            observed_at_epoch_ms:
              observation
                .observed_at_epoch_ms,
            clinical_order:
              null,
            observations: []
          };

          groups.push(group);
        }

        group.observations.push(
          observation
        );
      }

      return deepFreeze(
        groups.map(
          (group) => ({
            observed_at_epoch_ms:
              group
                .observed_at_epoch_ms,
            clinical_order:
              null,
            equal_time_tie:
              group
                .observations
                .length > 1,
            observations:
              [...group.observations]
          })
        )
      );
    }


    function displayModel(
      observation
    ) {
      if (
        !observation
        || typeof observation
          .instrument_key
          !== 'string'
      ) {
        fail('invalid_observation');
      }

      const instrument =
        registryByKey.get(
          observation
            .instrument_key
        );

      if (!instrument) {
        fail('unknown_instrument_key');
      }

      const extractList =
        (name) =>
          (
            instrument[name]
            || []
          ).map(
            (field) =>
              extractRegisteredField(
                observation,
                field
              )
          );

      const plotGroups =
        (
          instrument.plot_groups
          || []
        ).map(
          (plotGroup) => ({
            group_id:
              plotGroup.group_id,
            unit:
              plotGroup.unit,
            render:
              plotGroup.render,
            connect_points:
              plotGroup
                .connect_points,
            null_policy:
              plotGroup.null_policy,
            fields:
              plotGroup.fields.map(
                (field) => {
                  const extracted =
                    extractRegisteredField(
                      observation,
                      field
                    );

                  const numeric =
                    extracted.present
                    && typeof extracted.value
                      === 'number'
                    && Number.isFinite(
                      extracted.value
                    );

                  return {
                    ...extracted,
                    plot_value:
                      numeric
                        ? extracted.value
                        : null,
                    gap:
                      !numeric
                  };
                }
              )
          })
        );

      return snapshotClinicalJson({
        instrument_key:
          observation
            .instrument_key,
        runtime_key:
          observation
            .runtime_key,
        observed_at:
          observation
            .observed_at,
        captured_at:
          observation
            .captured_at,
        execution_source:
          observation
            .execution_source,
        summary_fields:
          extractList(
            'summary_fields'
          ),
        component_fields:
          extractList(
            'component_fields'
          ),
        context_fields:
          extractList(
            'context_fields'
          ),
        plot_groups:
          plotGroups
      });
    }


    function clearInstrument(
      instrumentKey
    ) {
      if (
        !registryByKey.has(
          instrumentKey
        )
      ) {
        fail('unknown_instrument_key');
      }

      series.delete(
        instrumentKey
      );
    }


    function clearAll() {
      series.clear();
    }


    return Object.freeze({
      addObservation,
      chronologyGroups,
      displayModel,
      clearInstrument,
      clearAll
    });
  }


  const api =
    Object.freeze({
      parseObservedAt,
      snapshotClinicalJson,
      createStore
    });


  if (
    typeof module !== 'undefined'
    && module.exports
  ) {
    module.exports = api;
  }


  if (
    typeof globalThis
    !== 'undefined'
  ) {
    globalThis
      .SerialTrendsRuntime =
        api;
  }
})();
