(() => {
  'use strict';

  const STORAGE_KEY =
    'clinical-reference-v2-ui-session-v1';

  const SCHEMA_VERSION = 1;


  const NAVIGATION_VALUES =
    Object.freeze({
      tab:
        new Set([
          'sae',
          'policy',
          'pcdt',
          'calc',
          'scales',
          'trends'
        ]),

      calc_group:
        new Set([
          'drip',
          'medication',
          'bmi',
          'paediatrics',
          'renal',
          'falls-function',
          'metabolic',
          'oxygenation',
          'hemodynamics',
          'obstetrics'
        ]),

      scale_group:
        new Set([
          'news2',
          'neurological',
          'apgar'
        ]),

      policy:
        new Set([
          'PNAISM',
          'PNAISH',
          'PNAISC',
          'PNAB',
          'PNSTT',
          'PNSPI',
          'PNSIPN'
        ])
    });


  const TOOL_RESULT_SURFACES =
    Object.freeze({
      'drip-form': [
        'drip-result'
      ],

      'meds-form': [
        'med-result'
      ],

      'bmi-form': [
        'bmi-result'
      ],

      'ped-form': [
        'ped-result'
      ],

      'crcl-form': [
        'crcl-result'
      ],

      'caderneta-falls-form': [
        'caderneta-falls-result'
      ],

      'ivcf20-form': [
        'ivcf20-result'
      ],

      'steadi-tug-form': [
        'steadi-tug-result'
      ],

      'steadi-chair-form': [
        'steadi-chair-result'
      ],

      'steadi-balance-form': [
        'steadi-balance-result'
      ],

      'steadi-orthostatic-form': [
        'steadi-orthostatic-result'
      ],

      'growth-form': [
        'growth-result'
      ],

      'metabolic-form': [
        'metabolic-result'
      ],

      'methanol-form': [
        'methanol-result'
      ],

      'oxygenation-form': [
        'oxygenation-result'
      ],

      'hemodynamics-form': [
        'hemodynamics-result'
      ],

      'renal-egfr-form': [
        'renal-egfr-result'
      ],

      'renal-ckd-form': [
        'renal-ckd-result'
      ],

      'renal-aki-form': [
        'renal-aki-result'
      ],

      'naegele-form': [
        'naegele-result'
      ],

      'mcdonald-form': [
        'mcdonald-result'
      ],

      'news2-form': [
        'news2-result'
      ],

      'glasgow-form': [
        'glasgow-result'
      ],

      'gcsp-form': [
        'gcsp-result'
      ],

      'four-form': [
        'four-result'
      ],

      'apgar-form': [
        'apgar-total',
        'apgar-note'
      ]
    });


  const TOOL_SERIAL_KEYS =
    Object.freeze({
      'metabolic-form':
        'acid_base_metabolic',

      'caderneta-falls-form':
        'brazil_caderneta_falls',

      'methanol-form':
        'brazil_methanol',

      'renal-ckd-form':
        'ckd_classification',

      'renal-egfr-form':
        'egfr_ckd_epi_2021',

      'four-form':
        'four_score',

      'glasgow-form':
        'gcs',

      'gcsp-form':
        'gcs_p',

      'hemodynamics-form':
        'hemodynamics',

      'ivcf20-form':
        'ivcf20',

      'renal-aki-form':
        'kdigo_aki',

      'news2-form':
        'news2',

      'oxygenation-form':
        'oxygenation',

      'steadi-chair-form':
        'steadi_chair_stand_30s',

      'steadi-balance-form':
        'steadi_four_stage_balance',

      'steadi-orthostatic-form':
        'steadi_orthostatic_bp',

      'steadi-tug-form':
        'steadi_tug',

      'growth-form':
        'who_growth'
    });


  function blankState() {
    return {
      schema_version:
        SCHEMA_VERSION,

      navigation: {
        tab:
          null,

        calc_group:
          null,

        scale_group:
          null,

        policy:
          null
      },

      tools:
        {},

      serial_captures:
        {}
    };
  }


  function isPlainObject(
    value
  ) {
    return (
      value !== null
      && typeof value === 'object'
      && !Array.isArray(value)
    );
  }


  function cloneJson(
    value
  ) {
    return JSON.parse(
      JSON.stringify(
        value
      )
    );
  }


  function loadState() {
    const fallback =
      blankState();

    try {
      const raw =
        sessionStorage.getItem(
          STORAGE_KEY
        );

      if (!raw) {
        return fallback;
      }

      const parsed =
        JSON.parse(
          raw
        );

      if (
        !isPlainObject(parsed)
        || parsed.schema_version
          !== SCHEMA_VERSION
      ) {
        sessionStorage.removeItem(
          STORAGE_KEY
        );

        return fallback;
      }

      if (
        isPlainObject(
          parsed.navigation
        )
      ) {
        for (
          const key
          of Object.keys(
            fallback.navigation
          )
        ) {
          const value =
            parsed.navigation[
              key
            ];

          if (
            typeof value
              === 'string'
            && NAVIGATION_VALUES[
              key
            ]?.has(
              value
            )
          ) {
            fallback.navigation[
              key
            ] = value;
          }
        }
      }

      if (
        isPlainObject(
          parsed.tools
        )
      ) {
        for (
          const formId
          of Object.keys(
            TOOL_RESULT_SURFACES
          )
        ) {
          if (
            isPlainObject(
              parsed.tools[
                formId
              ]
            )
          ) {
            fallback.tools[
              formId
            ] =
              parsed.tools[
                formId
              ];
          }
        }
      }

      if (
        isPlainObject(
          parsed.serial_captures
        )
      ) {
        const allowed =
          new Set(
            Object.values(
              TOOL_SERIAL_KEYS
            )
          );

        for (
          const [
            key,
            capture
          ]
          of Object.entries(
            parsed.serial_captures
          )
        ) {
          if (
            allowed.has(
              key
            )
            && isPlainObject(
              capture
            )
            && [
              'api',
              'offline'
            ].includes(
              capture.source
            )
            && capture.request
              !== null
            && capture.request
              !== undefined
            && capture.result
              !== null
            && capture.result
              !== undefined
          ) {
            fallback
              .serial_captures[
                key
              ] =
                cloneJson(
                  capture
                );
          }
        }
      }

      return fallback;

    } catch (_) {
      return fallback;
    }
  }


  let state =
    loadState();

  let restoring =
    false;

  const baselineSurfaces =
    new Map();


  function persistState() {
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(
          state
        )
      );

      return true;

    } catch (_) {
      return false;
    }
  }


  function getNavigation(
    key
  ) {
    if (
      !Object.prototype
        .hasOwnProperty.call(
          state.navigation,
          key
        )
    ) {
      return null;
    }

    return state.navigation[
      key
    ];
  }


  function setNavigation(
    key,
    value
  ) {
    const allowed =
      NAVIGATION_VALUES[
        key
      ];

    if (
      !allowed
      || !allowed.has(
        value
      )
    ) {
      return false;
    }

    state.navigation[
      key
    ] = value;

    return persistState();
  }


  function snapshotControls(
    form
  ) {
    const controls = {};

    form
      .querySelectorAll(
        'input[id], select[id]'
      )
      .forEach(
        (element) => {
          if (
            element.type === 'file'
            || element.type === 'button'
            || element.type === 'submit'
            || element.type === 'reset'
            || element.type === 'hidden'
          ) {
            return;
          }

          if (
            element.type === 'checkbox'
            || element.type === 'radio'
          ) {
            controls[
              element.id
            ] = {
              kind:
                'checked',

              checked:
                Boolean(
                  element.checked
                )
            };

            return;
          }

          if (
            element instanceof
              HTMLSelectElement
            && element.multiple
          ) {
            controls[
              element.id
            ] = {
              kind:
                'multiple',

              values:
                Array.from(
                  element
                    .selectedOptions
                ).map(
                  (option) =>
                    option.value
                )
            };

            return;
          }

          controls[
            element.id
          ] = {
            kind:
              'value',

            value:
              String(
                element.value
              )
          };
        }
      );

    return controls;
  }


  function restoreControls(
    form,
    controls
  ) {
    if (
      !isPlainObject(
        controls
      )
    ) {
      return;
    }

    for (
      const [
        id,
        saved
      ]
      of Object.entries(
        controls
      )
    ) {
      if (
        !isPlainObject(
          saved
        )
      ) {
        continue;
      }

      const element =
        document.getElementById(
          id
        );

      if (
        !element
        || !form.contains(
          element
        )
      ) {
        continue;
      }

      if (
        saved.kind
        === 'checked'
      ) {
        element.checked =
          Boolean(
            saved.checked
          );

        continue;
      }

      if (
        saved.kind
          === 'multiple'
        && element instanceof
          HTMLSelectElement
        && Array.isArray(
          saved.values
        )
      ) {
        const wanted =
          new Set(
            saved.values.map(
              String
            )
          );

        for (
          const option
          of element.options
        ) {
          option.selected =
            wanted.has(
              option.value
            );
        }

        continue;
      }

      if (
        saved.kind
          === 'value'
        && typeof saved.value
          === 'string'
      ) {
        element.value =
          saved.value;
      }
    }
  }


  function sanitiseResultHtml(
    html
  ) {
    const template =
      document.createElement(
        'template'
      );

    template.innerHTML =
      String(
        html ?? ''
      );

    template.content
      .querySelectorAll(
        'script, style, iframe, object, embed, link, meta, form, input, button'
      )
      .forEach(
        (element) =>
          element.remove()
      );

    template.content
      .querySelectorAll('*')
      .forEach(
        (element) => {
          for (
            const attribute
            of Array.from(
              element.attributes
            )
          ) {
            const name =
              attribute.name
                .toLowerCase();

            const allowed =
              (
                name === 'class'
                || name === 'lang'
                || name === 'dir'
                || name === 'title'
                || name.startsWith(
                  'aria-'
                )
              );

            if (!allowed) {
              element.removeAttribute(
                attribute.name
              );
            }
          }
        }
      );

    return template.innerHTML;
  }


  function safeClassName(
    value
  ) {
    const text =
      String(
        value ?? ''
      );

    return (
      /^[A-Za-z0-9_:/.[\]()%\-\s]+$/
        .test(
          text
        )
      ? text
      : ''
    );
  }


  function snapshotSurfaces(
    formId
  ) {
    const result = {};

    for (
      const id
      of TOOL_RESULT_SURFACES[
        formId
      ]
      || []
    ) {
      const element =
        document.getElementById(
          id
        );

      if (!element) {
        continue;
      }

      result[
        id
      ] = {
        class_name:
          element.className,

        html:
          sanitiseResultHtml(
            element.innerHTML
          )
      };
    }

    return result;
  }


  function restoreSurfaces(
    surfaces
  ) {
    if (
      !isPlainObject(
        surfaces
      )
    ) {
      return;
    }

    for (
      const [
        id,
        saved
      ]
      of Object.entries(
        surfaces
      )
    ) {
      if (
        !isPlainObject(
          saved
        )
      ) {
        continue;
      }

      const element =
        document.getElementById(
          id
        );

      if (!element) {
        continue;
      }

      const className =
        safeClassName(
          saved.class_name
        );

      if (className) {
        element.className =
          className;
      }

      element.innerHTML =
        sanitiseResultHtml(
          saved.html
        );

      if (
        element.dataset
      ) {
        delete element.dataset
          .clinicalResultStatus;
      }
    }
  }


  function resultIsSuccessful(
    formId
  ) {
    if (
      formId
      === 'apgar-form'
    ) {
      const total =
        document.getElementById(
          'apgar-total'
        );

      return Boolean(
        total
        && total.textContent
          .trim()
        && total.textContent
          .trim()
          !== '—'
      );
    }

    const resultId =
      TOOL_RESULT_SURFACES[
        formId
      ]?.[0];

    const element =
      resultId
        ? document.getElementById(
            resultId
          )
        : null;

    return Boolean(
      element
      && element.dataset
        ?.clinicalResultStatus
        !== 'error'
      && !element.classList
        .contains(
          'hidden'
        )
      && element.textContent
        .trim()
        .length
        > 0
    );
  }


  function validCapture(
    capture
  ) {
    return Boolean(
      capture
      && capture.request
        !== null
      && capture.request
        !== undefined
      && capture.result
        !== null
      && capture.result
        !== undefined
      && [
        'api',
        'offline'
      ].includes(
        capture.source
      )
    );
  }


  function currentSerialCapture(
    formId
  ) {
    const instrumentKey =
      TOOL_SERIAL_KEYS[
        formId
      ];

    if (!instrumentKey) {
      return null;
    }

    const capture =
      globalThis
        .ClinicalSerialCaptureBridge
        ?.currentLive?.(
          instrumentKey
        );

    if (
      !validCapture(
        capture
      )
    ) {
      return null;
    }

    return cloneJson(
      capture
    );
  }


  function saveToolState(
    formId
  ) {
    if (
      restoring
      || !Object.prototype
        .hasOwnProperty.call(
          TOOL_RESULT_SURFACES,
          formId
        )
      || !resultIsSuccessful(
        formId
      )
    ) {
      return false;
    }

    const form =
      document.getElementById(
        formId
      );

    if (!form) {
      return false;
    }

    state.tools[
      formId
    ] = {
      controls:
        snapshotControls(
          form
        ),

      surfaces:
        snapshotSurfaces(
          formId
        )
    };

    const instrumentKey =
      TOOL_SERIAL_KEYS[
        formId
      ];

    if (instrumentKey) {
      const capture =
        currentSerialCapture(
          formId
        );

      if (capture) {
        state.serial_captures[
          instrumentKey
        ] = capture;
      }
    }

    return persistState();
  }


  function captureBaselineSurfaces() {
    for (
      const [
        formId,
        resultIds
      ]
      of Object.entries(
        TOOL_RESULT_SURFACES
      )
    ) {
      const baseline = {};

      for (
        const id
        of resultIds
      ) {
        const element =
          document.getElementById(
            id
          );

        if (!element) {
          continue;
        }

        baseline[
          id
        ] = {
          class_name:
            element.className,

          html:
            element.innerHTML
        };
      }

      baselineSurfaces.set(
        formId,
        baseline
      );
    }
  }


  function restoreSerialCaptures() {
    const bridge =
      globalThis
        .ClinicalSerialCaptureBridge;

    if (
      !bridge
      || typeof bridge.restore
        !== 'function'
    ) {
      return;
    }

    for (
      const [
        instrumentKey,
        capture
      ]
      of Object.entries(
        state.serial_captures
      )
    ) {
      try {
        bridge.restore(
          instrumentKey,
          cloneJson(
            capture
          )
        );

      } catch (_) {}
    }
  }


  function restoreToolStates() {
    restoring = true;

    try {
      for (
        const formId
        of Object.keys(
          TOOL_RESULT_SURFACES
        )
      ) {
        const saved =
          state.tools[
            formId
          ];

        if (
          !isPlainObject(
            saved
          )
        ) {
          continue;
        }

        const form =
          document.getElementById(
            formId
          );

        if (!form) {
          continue;
        }

        restoreControls(
          form,
          saved.controls
        );

        restoreSurfaces(
          saved.surfaces
        );
      }

    } finally {
      restoring = false;
    }
  }


  function clearToolState(
    formId
  ) {
    delete state.tools[
      formId
    ];

    const instrumentKey =
      TOOL_SERIAL_KEYS[
        formId
      ];

    if (instrumentKey) {
      delete state.serial_captures[
        instrumentKey
      ];

      try {
        globalThis
          .ClinicalSerialCaptureBridge
          ?.clear?.(
            instrumentKey
          );

      } catch (_) {}
    }

    const baseline =
      baselineSurfaces.get(
        formId
      );

    restoring = true;

    try {
      restoreSurfaces(
        baseline
      );

    } finally {
      restoring = false;
    }

    persistState();
  }


  function resetLabel() {
    return (
      globalThis
        .ClinicalI18n
        ?.t?.(
          'tool.reset'
        )
      || (
        document.documentElement.lang
        === 'en-GB'
          ? 'Reset'
          : 'Redefinir'
      )
    );
  }


  function applyResetLabels() {
    document
      .querySelectorAll(
        '[data-clinical-tool-reset]'
      )
      .forEach(
        (button) => {
          button.textContent =
            resetLabel();
        }
      );
  }


  function ensureResetButtons() {
    for (
      const formId
      of Object.keys(
        TOOL_RESULT_SURFACES
      )
    ) {
      const form =
        document.getElementById(
          formId
        );

      if (
        !form
        || form.querySelector(
          '[data-clinical-tool-reset]'
        )
      ) {
        continue;
      }

      const row =
        document.createElement(
          'div'
        );

      row.className =
        'clinical-tool-reset-row';

      const button =
        document.createElement(
          'button'
        );

      button.type =
        'reset';

      button.className =
        'clinical-tool-reset-button';

      button.dataset
        .clinicalToolReset =
          formId;

      button.dataset.i18n =
        'tool.reset';

      button.textContent =
        resetLabel();

      row.appendChild(
        button
      );

      form.appendChild(
        row
      );
    }
  }


  function wireResultObservers() {
    for (
      const [
        formId,
        resultIds
      ]
      of Object.entries(
        TOOL_RESULT_SURFACES
      )
    ) {
      for (
        const resultId
        of resultIds
      ) {
        const element =
          document.getElementById(
            resultId
          );

        if (!element) {
          continue;
        }

        const observer =
          new MutationObserver(
            () => {
              if (
                !restoring
              ) {
                saveToolState(
                  formId
                );
              }
            }
          );

        observer.observe(
          element,
          {
            childList:
              true,

            subtree:
              true,

            characterData:
              true,

            attributes:
              true,

            attributeFilter: [
              'class'
            ]
          }
        );
      }
    }
  }


  function wireResetEvents() {
    for (
      const formId
      of Object.keys(
        TOOL_RESULT_SURFACES
      )
    ) {
      const form =
        document.getElementById(
          formId
        );

      form?.addEventListener(
        'reset',
        () => {
          setTimeout(
            () => {
              clearToolState(
                formId
              );

              const first =
                form.querySelector(
                  'input:not([type="hidden"]):not([disabled]), select:not([disabled])'
                );

              first?.focus?.();
            },
            0
          );
        }
      );
    }
  }


  function clearPendingErrorMarker(
    formId
  ) {
    for (
      const resultId
      of TOOL_RESULT_SURFACES[
        formId
      ]
      || []
    ) {
      const element =
        document.getElementById(
          resultId
        );

      if (
        element?.dataset
      ) {
        delete element.dataset
          .clinicalResultStatus;
      }
    }
  }


  function wireSubmitPreflight() {
    document.addEventListener(
      'submit',
      (event) => {
        const formId =
          event.target?.id;

        if (
          formId
          && Object.prototype
            .hasOwnProperty.call(
              TOOL_RESULT_SURFACES,
              formId
            )
        ) {
          clearPendingErrorMarker(
            formId
          );
        }
      },
      true
    );
  }


  function restoreNavigation() {
    const tab =
      state.navigation.tab;

    if (tab) {
      document
        .querySelector(
          `[data-tab="${tab}"]`
        )
        ?.click?.();
    }

    const policy =
      state.navigation.policy;

    if (policy) {
      document
        .querySelector(
          `[data-policy="${policy}"]`
        )
        ?.click?.();
    }
  }


  function wireHomeLink() {
    document
      .getElementById(
        'brand-home'
      )
      ?.addEventListener(
        'click',
        () => {
          setNavigation(
            'tab',
            'sae'
          );
        }
      );
  }


  function getSerialCapture(
    instrumentKey
  ) {
    const capture =
      state.serial_captures[
        instrumentKey
      ];

    return (
      validCapture(
        capture
      )
      ? cloneJson(
          capture
        )
      : null
    );
  }


  function init() {
    captureBaselineSurfaces();
    ensureResetButtons();
    restoreSerialCaptures();
    restoreToolStates();
    wireResultObservers();
    wireResetEvents();
    wireHomeLink();
    applyResetLabels();
  }


  wireSubmitPreflight();

  document.addEventListener(
    'DOMContentLoaded',
    init
  );


  globalThis.addEventListener?.(
    'clinical-language-change',
    applyResetLabels
  );


  globalThis.ClinicalUiSession =
    Object.freeze({
      storageKey:
        STORAGE_KEY,

      getNavigation,
      setNavigation,
      restoreNavigation,
      getSerialCapture,

      persistCurrentTool:
        saveToolState
    });
})();
