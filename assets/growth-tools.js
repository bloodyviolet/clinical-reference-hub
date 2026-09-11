(() => {
  'use strict';


  const DAYS_PER_MONTH =
    30.4375;


  const REF_BASE =
    '/assets/reference/who-growth';


  const WHO2006_COMMIT =
    'b776d8a12b1c97369c748b561159fd2ec4f4db58';


  const WHO2007_COMMIT =
    '7cfcdb39026e9a55de55732bc3cf14c82261bcf7';


  const FILES = Object.freeze({
    wfa06:
      'who2006_weight_for_age.json',

    lha06:
      'who2006_length_height_for_age.json',

    bmi06:
      'who2006_bmi_for_age.json',

    hc06:
      'who2006_head_circumference_for_age.json',

    wfl06:
      'who2006_weight_for_length.json',

    wfh06:
      'who2006_weight_for_height.json',

    wfa07:
      'who2007_weight_for_age.json',

    hfa07:
      'who2007_height_for_age.json',

    bmi07:
      'who2007_bmi_for_age.json',

    brazil:
      'BRAZIL_SISVAN.json'
  });


  let growthBundlePromise =
    null;


  function halfEvenRound(
    value,
    digits = 0
  ) {
    if (!Number.isFinite(value)) {
      return value;
    }


    const factor =
      10 ** digits;

    const scaled =
      value * factor;

    const lower =
      Math.floor(scaled);

    const fraction =
      scaled - lower;

    const tolerance =
      1e-11;


    let roundedInteger;


    if (
      fraction
      > 0.5 + tolerance
    ) {
      roundedInteger =
        lower + 1;

    } else if (
      fraction
      < 0.5 - tolerance
    ) {
      roundedInteger =
        lower;

    } else {
      roundedInteger =
        Math.abs(lower % 2) === 0
          ? lower
          : lower + 1;
    }


    return (
      roundedInteger
      / factor
    );
  }


  function roundHalfUpPositive(
    value
  ) {
    if (
      !Number.isFinite(value)
      || value < 0
    ) {
      throw new Error(
        'invalid_age'
      );
    }


    const base =
      Math.floor(value);


    return (
      value - base >= 0.5
        ? base + 1
        : base
    );
  }


  async function cachedReferenceResponse(
    url
  ) {
    if (
      typeof caches === 'undefined'
    ) {
      return null;
    }


    try {
      const response =
        await caches.match(
          url,
          {
            ignoreSearch: true
          }
        );


      return (
        response
        && response.ok
          ? response
          : null
      );

    } catch (_) {
      return null;
    }
  }


  async function loadReferenceJson(
    filename
  ) {
    const url =
      `${REF_BASE}/${filename}`;


    let response =
      await cachedReferenceResponse(
        url
      );


    if (!response) {
      response =
        await fetch(
          url,
          {
            cache: 'force-cache'
          }
        );
    }


    if (
      !response
      || !response.ok
    ) {
      throw new Error(
        `growth_reference_unavailable:${filename}`
      );
    }


    return response.json();
  }


  function ageIndex(
    rows
  ) {
    const result =
      new Map();


    for (const row of rows) {
      result.set(
        `${row.sex}|${row.age}`,
        row
      );
    }


    return result;
  }


  function sizeIndex(
    rows,
    field
  ) {
    const result =
      new Map();


    for (const row of rows) {
      result.set(
        `${row.sex}|${Number(row[field]).toFixed(1)}`,
        row
      );
    }


    return result;
  }


  async function loadGrowthBundle() {
    if (!growthBundlePromise) {
      growthBundlePromise = (
        async () => {
          const entries =
            await Promise.all(
              Object.entries(FILES)
                .map(
                  async ([key, filename]) => [
                    key,
                    await loadReferenceJson(
                      filename
                    )
                  ]
                )
            );


          const data =
            Object.fromEntries(
              entries
            );


          return {
            data,

            age: {
              wfa06:
                ageIndex(data.wfa06),

              lha06:
                ageIndex(data.lha06),

              bmi06:
                ageIndex(data.bmi06),

              hc06:
                ageIndex(data.hc06),

              wfa07:
                ageIndex(data.wfa07),

              hfa07:
                ageIndex(data.hfa07),

              bmi07:
                ageIndex(data.bmi07)
            },

            size: {
              wfl06:
                sizeIndex(
                  data.wfl06,
                  'length'
                ),

              wfh06:
                sizeIndex(
                  data.wfh06,
                  'height'
                )
            }
          };
        }
      )().catch(
        error => {
          growthBundlePromise =
            null;

          throw error;
        }
      );
    }


    return growthBundlePromise;
  }


  function sexCode(
    value
  ) {
    const normalized =
      String(value)
        .trim()
        .toLowerCase();


    if (
      normalized === 'male'
      || normalized === 'm'
      || normalized === '1'
    ) {
      return 1;
    }


    if (
      normalized === 'female'
      || normalized === 'f'
      || normalized === '2'
    ) {
      return 2;
    }


    throw new Error(
      'invalid_sex'
    );
  }


  function prepareAge(
    ageValue,
    ageUnit
  ) {
    if (
      !Number.isFinite(ageValue)
      || ageValue < 0
    ) {
      throw new Error(
        'invalid_age'
      );
    }


    if (ageUnit === 'days') {
      return {
        ageDays:
          roundHalfUpPositive(
            ageValue
          ),

        ageMonths:
          ageValue
          / DAYS_PER_MONTH
      };
    }


    if (ageUnit === 'months') {
      return {
        ageDays:
          roundHalfUpPositive(
            ageValue
            * DAYS_PER_MONTH
          ),

        ageMonths:
          ageValue
      };
    }


    throw new Error(
      'invalid_age_unit'
    );
  }


  function basicLmsZ(
    value,
    l,
    m,
    s
  ) {
    if (
      !Number.isFinite(value)
      || value <= 0
    ) {
      throw new Error(
        'invalid_growth_measurement'
      );
    }


    if (
      Math.abs(l)
      <= 1e-12
    ) {
      return (
        Math.log(
          value / m
        )
        / s
      );
    }


    return (
      (
        (value / m) ** l
        - 1
      )
      / (
        s * l
      )
    );
  }


  function sdValue(
    sd,
    l,
    m,
    s
  ) {
    if (
      Math.abs(l)
      <= 1e-12
    ) {
      return (
        m
        * Math.exp(
          s * sd
        )
      );
    }


    return (
      m
      * (
        1
        + l * s * sd
      ) ** (
        1 / l
      )
    );
  }


  function adjustedLmsZ(
    value,
    l,
    m,
    s
  ) {
    const z =
      basicLmsZ(
        value,
        l,
        m,
        s
      );


    if (z > 3) {
      const sd3 =
        sdValue(
          3,
          l,
          m,
          s
        );

      const sd2 =
        sdValue(
          2,
          l,
          m,
          s
        );


      return (
        3
        + (
          value - sd3
        )
        / (
          sd3 - sd2
        )
      );
    }


    if (z < -3) {
      const sdNeg3 =
        sdValue(
          -3,
          l,
          m,
          s
        );

      const sdNeg2 =
        sdValue(
          -2,
          l,
          m,
          s
        );


      return (
        -3
        + (
          value - sdNeg3
        )
        / (
          sdNeg2 - sdNeg3
        )
      );
    }


    return z;
  }


  function erfApprox(
    value
  ) {
    const sign =
      value < 0
        ? -1
        : 1;

    const x =
      Math.abs(value);

    const t =
      1
      / (
        1
        + 0.3275911 * x
      );

    const polynomial =
      (
        (
          (
            (
              1.061405429 * t
              - 1.453152027
            ) * t
            + 1.421413741
          ) * t
          - 0.284496736
        ) * t
        + 0.254829592
      ) * t;

    const y =
      1
      - polynomial
      * Math.exp(
        -x * x
      );


    return sign * y;
  }


  function percentile(
    rawZ
  ) {
    if (
      rawZ < -3
      || rawZ > 3
    ) {
      return null;
    }


    if (
      Math.abs(rawZ)
      <= 1e-14
    ) {
      return 50;
    }


    const result =
      0.5
      * (
        1
        + erfApprox(
          rawZ
          / Math.sqrt(2)
        )
      )
      * 100;


    return halfEvenRound(
      result,
      2
    );
  }


  function lmsFromRow(
    row
  ) {
    return {
      l: Number(row.l),
      m: Number(row.m),
      s: Number(row.s)
    };
  }


  function who2006AgeLms(
    index,
    sex,
    ageDays
  ) {
    const row =
      index.get(
        `${sex}|${ageDays}`
      );


    return row
      ? lmsFromRow(row)
      : null;
  }


  function who2007Lms(
    index,
    sex,
    ageMonths,
    upperExclusive
  ) {
    if (
      ageMonths < 60
      || ageMonths >= upperExclusive
    ) {
      return null;
    }


    const lowAge =
      Math.trunc(
        ageMonths
      );

    const upperAge =
      Math.trunc(
        ageMonths + 1
      );

    const diff =
      ageMonths - lowAge;


    const low =
      index.get(
        `${sex}|${lowAge}`
      );


    if (!low) {
      return null;
    }


    if (diff <= 0) {
      return lmsFromRow(low);
    }


    const upper =
      index.get(
        `${sex}|${upperAge}`
      );


    if (!upper) {
      return null;
    }


    return {
      l:
        Number(low.l)
        + diff
        * (
          Number(upper.l)
          - Number(low.l)
        ),

      m:
        Number(low.m)
        + diff
        * (
          Number(upper.m)
          - Number(low.m)
        ),

      s:
        Number(low.s)
        + diff
        * (
          Number(upper.s)
          - Number(low.s)
        )
    };
  }


  function who2006SizeLms(
    index,
    sex,
    sizeCm
  ) {
    const lowSize =
      Math.trunc(
        sizeCm * 10
      )
      / 10;


    const upperSize =
      Math.trunc(
        sizeCm * 10
        + 1
      )
      / 10;


    const diff =
      (
        sizeCm - lowSize
      )
      / 0.1;


    const low =
      index.get(
        `${sex}|${lowSize.toFixed(1)}`
      );


    if (!low) {
      return null;
    }


    if (
      diff <= 1e-12
    ) {
      return lmsFromRow(low);
    }


    const upper =
      index.get(
        `${sex}|${upperSize.toFixed(1)}`
      );


    if (!upper) {
      return null;
    }


    return {
      l:
        Number(low.l)
        + diff
        * (
          Number(upper.l)
          - Number(low.l)
        ),

      m:
        Number(low.m)
        + diff
        * (
          Number(upper.m)
          - Number(low.m)
        ),

      s:
        Number(low.s)
        + diff
        * (
          Number(upper.s)
          - Number(low.s)
        )
    };
  }


  function classification(
    code,
    labelPt,
    labelEn
  ) {
    return {
      code,
      label_pt:
        labelPt,
      label_en:
        labelEn
    };
  }


  function whoClassification(
    indicator,
    ageMonths,
    z
  ) {
    if (
      indicator
      === 'head_circumference_for_age'
    ) {
      return null;
    }


    if (
      indicator
      === 'length_height_for_age'
    ) {
      if (z < -3) {
        return classification(
          'severely_stunted',
          'Déficit grave de estatura',
          'Severely stunted'
        );
      }

      if (z < -2) {
        return classification(
          'stunted',
          'Déficit de estatura',
          'Stunted'
        );
      }

      return null;
    }


    if (
      indicator
      === 'weight_for_age'
    ) {
      if (z < -3) {
        return classification(
          'severely_underweight',
          'Peso muito baixo para a idade',
          'Severely underweight'
        );
      }

      if (z < -2) {
        return classification(
          'underweight',
          'Baixo peso para a idade',
          'Underweight'
        );
      }

      return null;
    }


    if (
      ageMonths < 60
      && (
        indicator
        === 'weight_for_length_height'
        || indicator
        === 'bmi_for_age'
      )
    ) {
      if (z < -3) {
        return classification(
          'severely_wasted',
          'Magreza grave',
          'Severely wasted'
        );
      }

      if (z < -2) {
        return classification(
          'wasted',
          'Magreza',
          'Wasted'
        );
      }

      if (z > 3) {
        return classification(
          'obesity',
          'Obesidade',
          'Obesity'
        );
      }

      if (z > 2) {
        return classification(
          'overweight',
          'Sobrepeso',
          'Overweight'
        );
      }

      if (z > 1) {
        return classification(
          'possible_risk_overweight',
          'Possível risco de sobrepeso',
          'Possible risk of overweight'
        );
      }

      return null;
    }


    if (
      ageMonths >= 60
      && indicator
      === 'bmi_for_age'
    ) {
      if (z < -3) {
        return classification(
          'severe_thinness',
          'Magreza acentuada',
          'Severe thinness'
        );
      }

      if (z < -2) {
        return classification(
          'thinness',
          'Magreza',
          'Thinness'
        );
      }

      if (z > 2) {
        return classification(
          'obesity',
          'Obesidade',
          'Obesity'
        );
      }

      if (z > 1) {
        return classification(
          'overweight',
          'Sobrepeso',
          'Overweight'
        );
      }

      return null;
    }


    return null;
  }


  function bandMatches(
    band,
    z
  ) {
    if (
      Object.hasOwn(
        band,
        'z_min'
      )
    ) {
      if (
        band.z_min_inclusive
          ? z < band.z_min
          : z <= band.z_min
      ) {
        return false;
      }
    }


    if (
      Object.hasOwn(
        band,
        'z_max'
      )
    ) {
      if (
        band.z_max_inclusive
          ? z > band.z_max
          : z >= band.z_max
      ) {
        return false;
      }
    }


    return true;
  }


  function classifyBands(
    bands,
    z
  ) {
    if (!Array.isArray(bands)) {
      return null;
    }


    for (const band of bands) {
      if (
        bandMatches(
          band,
          z
        )
      ) {
        return classification(
          band.code,
          band.label_pt,
          band.label_en
        );
      }
    }


    return null;
  }


  function brazilBands(
    policy,
    indicator,
    ageMonths
  ) {
    const groups =
      policy.classifications;


    if (
      indicator
      === 'head_circumference_for_age'
    ) {
      return policy
        .head_circumference
        .classification;
    }


    if (ageMonths < 60) {
      const group =
        groups.under_5;


      if (
        indicator
        === 'weight_for_age'
      ) {
        return group.weight_for_age;
      }


      if (
        indicator
        === 'weight_for_length_height'
        || indicator
        === 'bmi_for_age'
      ) {
        return group
          .weight_for_length_height;
      }


      if (
        indicator
        === 'length_height_for_age'
      ) {
        return group
          .length_height_for_age;
      }


      return null;
    }


    if (ageMonths < 120) {
      if (
        indicator
        === 'weight_for_age'
      ) {
        return groups
          .under_5
          .weight_for_age;
      }


      if (
        indicator
        === 'bmi_for_age'
      ) {
        return groups
          .age_5_to_under_10
          .bmi_for_age;
      }


      if (
        indicator
        === 'length_height_for_age'
      ) {
        return groups
          .under_5
          .length_height_for_age;
      }


      return null;
    }


    if (
      indicator
      === 'bmi_for_age'
    ) {
      return groups
        .age_5_to_under_10
        .bmi_for_age;
    }


    if (
      indicator
      === 'length_height_for_age'
    ) {
      return groups
        .under_5
        .length_height_for_age;
    }


    return null;
  }


  function brazilClassification(
    policy,
    indicator,
    ageMonths,
    z
  ) {
    return classifyBands(
      brazilBands(
        policy,
        indicator,
        ageMonths
      ),
      z
    );
  }


  function plausibility(
    indicator,
    z
  ) {
    if (
      indicator
      === 'weight_for_age'
    ) {
      return {
        flag:
          z < -6
          || z > 5,

        range:
          '-6 <= z <= +5'
      };
    }


    if (
      indicator
      === 'length_height_for_age'
    ) {
      return {
        flag:
          Math.abs(z) > 6,

        range:
          '-6 <= z <= +6'
      };
    }


    return {
      flag:
        Math.abs(z) > 5,

      range:
        '-5 <= z <= +5'
    };
  }


  function indicatorResult(
    policy,
    indicator,
    rawZ,
    referenceStandard,
    referenceTable,
    ageMonths
  ) {
    const z =
      halfEvenRound(
        rawZ,
        2
      );


    const quality =
      plausibility(
        indicator,
        z
      );


    return {
      indicator,

      z_score:
        z,

      percentile:
        percentile(
          rawZ
        ),

      percentile_available:
        rawZ >= -3
        && rawZ <= 3,

      reference_standard:
        referenceStandard,

      reference_table:
        referenceTable,

      classification_who:
        whoClassification(
          indicator,
          ageMonths,
          z
        ),

      classification_br:
        brazilClassification(
          policy,
          indicator,
          ageMonths,
          z
        ),

      classification_z_basis:
        'WHO z-score rounded to 2 decimals',

      plausibility_flag:
        quality.flag,

      who_plausibility_range:
        quality.range
    };
  }


  async function calculateWhoGrowth(
    input
  ) {
    const bundle =
      await loadGrowthBundle();


    const sex =
      sexCode(
        input.sex
      );


    const {
      ageDays,
      ageMonths
    } = prepareAge(
      Number(
        input.age_value
      ),
      input.age_unit
    );


    const ageBasis =
      input.age_basis
      || 'chronological';


    if (
      ageBasis
      !== 'chronological'
      && ageBasis
      !== 'corrected'
    ) {
      throw new Error(
        'invalid_age_basis'
      );
    }


    const weight =
      input.weight_kg
      ?? null;

    const lenhei =
      input.length_height_cm
      ?? null;

    const head =
      input.head_circumference_cm
      ?? null;

    const position =
      input.measurement_position
      ?? null;

    const oedema =
      Boolean(
        input.oedema
      );


    if (
      weight === null
      && lenhei === null
      && head === null
    ) {
      throw new Error(
        'anthropometric_measurement_required'
      );
    }


    if (
      weight !== null
      && (
        !Number.isFinite(weight)
        || weight <= 0
      )
    ) {
      throw new Error(
        'invalid_weight'
      );
    }


    if (
      lenhei !== null
      && (
        !Number.isFinite(lenhei)
        || lenhei <= 0
      )
    ) {
      throw new Error(
        'invalid_length_height'
      );
    }


    if (
      head !== null
      && (
        !Number.isFinite(head)
        || head <= 0
      )
    ) {
      throw new Error(
        'invalid_head_circumference'
      );
    }


    if (
      lenhei !== null
      && position === null
    ) {
      throw new Error(
        'measurement_position_required'
      );
    }


    if (
      position !== null
      && position !== 'length'
      && position !== 'height'
    ) {
      throw new Error(
        'invalid_measurement_position'
      );
    }


    if (
      ageMonths >= 60
      && lenhei !== null
      && position !== 'height'
    ) {
      throw new Error(
        'who2007_requires_standing_height'
      );
    }


    let effectiveLenhei =
      lenhei;

    let effectivePosition =
      position;

    let adjustment =
      0;

    let measurementWarning =
      null;


    if (
      ageMonths < 60
      && lenhei !== null
    ) {
      if (
        ageMonths < 9
        && position === 'height'
      ) {
        measurementWarning =
          'height_under_9_months';

      } else if (
        ageDays < 731
        && position === 'height'
      ) {
        effectiveLenhei =
          lenhei + 0.7;

        effectivePosition =
          'length';

        adjustment =
          0.7;

      } else if (
        ageDays >= 731
        && position === 'length'
      ) {
        effectiveLenhei =
          lenhei - 0.7;

        effectivePosition =
          'height';

        adjustment =
          -0.7;
      }
    }


    const bmi =
      (
        weight !== null
        && effectiveLenhei !== null
      )
        ? (
            weight
            / (
              effectiveLenhei
              / 100
            ) ** 2
          )
        : null;


    const indicators = {
      weight_for_age:
        null,

      length_height_for_age:
        null,

      weight_for_length_height:
        null,

      bmi_for_age:
        null,

      head_circumference_for_age:
        null
    };


    const warningsPt = [];
    const warningsEn = [];


    if (
      ageBasis === 'corrected'
    ) {
      warningsPt.push(
        'Foi utilizada idade corrigida. A idade cronológica deve permanecer registrada separadamente.'
      );

      warningsEn.push(
        'Corrected age was used. Chronological age should remain recorded separately.'
      );
    }


    if (
      measurementWarning
      === 'height_under_9_months'
    ) {
      warningsPt.push(
        'Altura em pé informada para criança com menos de 9 meses: posição de mensuração inadequada segundo o controle de qualidade do WHO Anthro.'
      );

      warningsEn.push(
        'Standing height was supplied for a child younger than 9 months: this is an incorrect measurement position under WHO Anthro quality control.'
      );
    }


    if (oedema) {
      warningsPt.push(
        'Edema informado: indicadores dependentes de peso não foram calculados.'
      );

      warningsEn.push(
        'Oedema was reported: weight-related indicators were not calculated.'
      );
    }


    const policy =
      bundle.data.brazil;


    if (ageMonths < 60) {
      const reference =
        'WHO Child Growth Standards 2006';


      if (
        weight !== null
        && !oedema
      ) {
        const lms =
          who2006AgeLms(
            bundle.age.wfa06,
            sex,
            ageDays
          );


        if (lms) {
          indicators.weight_for_age =
            indicatorResult(
              policy,
              'weight_for_age',
              adjustedLmsZ(
                weight,
                lms.l,
                lms.m,
                lms.s
              ),
              reference,
              FILES.wfa06,
              ageMonths
            );
        }
      }


      if (
        effectiveLenhei !== null
      ) {
        const lms =
          who2006AgeLms(
            bundle.age.lha06,
            sex,
            ageDays
          );


        if (lms) {
          indicators
            .length_height_for_age =
              indicatorResult(
                policy,
                'length_height_for_age',
                basicLmsZ(
                  effectiveLenhei,
                  lms.l,
                  lms.m,
                  lms.s
                ),
                reference,
                FILES.lha06,
                ageMonths
              );
        }
      }


      if (
        bmi !== null
        && !oedema
      ) {
        const lms =
          who2006AgeLms(
            bundle.age.bmi06,
            sex,
            ageDays
          );


        if (lms) {
          indicators.bmi_for_age =
            indicatorResult(
              policy,
              'bmi_for_age',
              adjustedLmsZ(
                bmi,
                lms.l,
                lms.m,
                lms.s
              ),
              reference,
              FILES.bmi06,
              ageMonths
            );
        }
      }


      if (
        effectiveLenhei !== null
        && weight !== null
        && !oedema
      ) {
        let inDomain;
        let index;
        let filename;


        if (ageDays < 731) {
          inDomain =
            effectiveLenhei >= 45
            && effectiveLenhei <= 110;

          index =
            bundle.size.wfl06;

          filename =
            FILES.wfl06;

        } else {
          inDomain =
            effectiveLenhei >= 65
            && effectiveLenhei <= 120;

          index =
            bundle.size.wfh06;

          filename =
            FILES.wfh06;
        }


        if (inDomain) {
          const lms =
            who2006SizeLms(
              index,
              sex,
              effectiveLenhei
            );


          if (lms) {
            indicators
              .weight_for_length_height =
                indicatorResult(
                  policy,
                  'weight_for_length_height',
                  adjustedLmsZ(
                    weight,
                    lms.l,
                    lms.m,
                    lms.s
                  ),
                  reference,
                  filename,
                  ageMonths
                );
          }
        }
      }


      if (head !== null) {
        const lms =
          who2006AgeLms(
            bundle.age.hc06,
            sex,
            ageDays
          );


        if (lms) {
          const result =
            indicatorResult(
              policy,
              'head_circumference_for_age',
              basicLmsZ(
                head,
                lms.l,
                lms.m,
                lms.s
              ),
              reference,
              FILES.hc06,
              ageMonths
            );


          result
            .brazil_routine_monitoring_applicable =
              ageMonths <= 24;


          indicators
            .head_circumference_for_age =
              result;
        }
      }

    } else if (
      ageMonths < 229
    ) {
      const reference =
        'WHO Growth Reference 2007';


      if (
        weight !== null
        && !oedema
        && ageMonths < 121
      ) {
        const lms =
          who2007Lms(
            bundle.age.wfa07,
            sex,
            ageMonths,
            121
          );


        if (lms) {
          indicators.weight_for_age =
            indicatorResult(
              policy,
              'weight_for_age',
              adjustedLmsZ(
                weight,
                lms.l,
                lms.m,
                lms.s
              ),
              reference,
              FILES.wfa07,
              ageMonths
            );
        }
      }


      if (
        effectiveLenhei !== null
      ) {
        const lms =
          who2007Lms(
            bundle.age.hfa07,
            sex,
            ageMonths,
            229
          );


        if (lms) {
          indicators
            .length_height_for_age =
              indicatorResult(
                policy,
                'length_height_for_age',
                basicLmsZ(
                  effectiveLenhei,
                  lms.l,
                  lms.m,
                  lms.s
                ),
                reference,
                FILES.hfa07,
                ageMonths
              );
        }
      }


      if (
        bmi !== null
        && !oedema
      ) {
        const lms =
          who2007Lms(
            bundle.age.bmi07,
            sex,
            ageMonths,
            229
          );


        if (lms) {
          indicators.bmi_for_age =
            indicatorResult(
              policy,
              'bmi_for_age',
              adjustedLmsZ(
                bmi,
                lms.l,
                lms.m,
                lms.s
              ),
              reference,
              FILES.bmi07,
              ageMonths
            );
        }
      }


      if (ageMonths >= 120) {
        warningsPt.push(
          'Peso-para-idade não deve ser usado para classificação SISVAN a partir dos 10 anos.'
        );

        warningsEn.push(
          'Weight-for-age should not be used for SISVAN classification from age 10 years onward.'
        );
      }

    } else {
      warningsPt.push(
        'Idade fora do domínio nativo da referência WHO 2007 (<229 meses); nenhum LMS foi extrapolado.'
      );

      warningsEn.push(
        'Age is outside the native WHO 2007 reference domain (<229 months); no LMS value was extrapolated.'
      );
    }


    const headResult =
      indicators
        .head_circumference_for_age;


    if (
      headResult
      && ageMonths > 24
    ) {
      warningsPt.push(
        'A referência WHO para perímetro cefálico continua disponível, mas o acompanhamento rotineiro brasileiro é priorizado nos primeiros 24 meses.'
      );

      warningsEn.push(
        'The WHO head-circumference reference remains available, but Brazilian routine monitoring is prioritised in the first 24 months.'
      );
    }


    return {
      tool:
        'who_pediatric_growth',

      sex:
        sex === 1
          ? 'male'
          : 'female',

      age_input_value:
        Number(
          input.age_value
        ),

      age_input_unit:
        input.age_unit,

      age_basis:
        ageBasis,

      who_age_days:
        ageDays,

      who_age_months:
        halfEvenRound(
          ageMonths,
          4
        ),

      oedema,

      measurement_position_input:
        position,

      measurement_position_effective:
        effectivePosition,

      measurement_adjustment_cm:
        halfEvenRound(
          adjustment,
          1
        ),

      length_height_input_cm:
        lenhei === null
          ? null
          : halfEvenRound(
              lenhei,
              2
            ),

      length_height_effective_cm:
        effectiveLenhei === null
          ? null
          : halfEvenRound(
              effectiveLenhei,
              2
            ),

      bmi_kg_m2:
        bmi === null
          ? null
          : halfEvenRound(
              bmi,
              4
            ),

      indicators,

      warnings_pt:
        warningsPt,

      warnings_en:
        warningsEn,

      provenance: {
        who2006_commit:
          WHO2006_COMMIT,

        who2007_commit:
          WHO2007_COMMIT,

        brazil_policy:
          'Ministério da Saúde / SISVAN'
      }
    };
  }


  globalThis.ClinicalGrowthTools =
    Object.freeze({
      calculateWhoGrowth
    });
})();
