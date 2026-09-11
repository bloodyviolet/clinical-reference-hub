(() => {
  'use strict';


  function respirationScore(value) {
    if (value <= 8) return 3;
    if (value <= 11) return 1;
    if (value <= 20) return 0;
    if (value <= 24) return 2;
    return 3;
  }


  function spo2Scale1Score(value) {
    if (value <= 91) return 3;
    if (value <= 93) return 2;
    if (value <= 95) return 1;
    return 0;
  }


  function spo2Scale2Score(
    value,
    supplementalOxygen
  ) {
    if (value <= 83) return 3;
    if (value <= 85) return 2;
    if (value <= 87) return 1;
    if (value <= 92) return 0;

    if (!supplementalOxygen) {
      return 0;
    }

    if (value <= 94) return 1;
    if (value <= 96) return 2;

    return 3;
  }


  function systolicScore(value) {
    if (value <= 90) return 3;
    if (value <= 100) return 2;
    if (value <= 110) return 1;
    if (value <= 219) return 0;
    return 3;
  }


  function pulseScore(value) {
    if (value <= 40) return 3;
    if (value <= 50) return 1;
    if (value <= 90) return 0;
    if (value <= 110) return 1;
    if (value <= 130) return 2;
    return 3;
  }


  function temperatureScore(value) {
    if (value <= 35) return 3;
    if (value <= 36) return 1;
    if (value <= 38) return 0;
    if (value <= 39) return 1;
    return 2;
  }


  function responseFor(
    total,
    red
  ) {
    if (total >= 7) {
      return {
        aggregate_band: 'high',
        aggregate_label_pt:
          'Alto — total ≥7',
        aggregate_label_en:
          'High — total ≥7',

        trigger_code: 'high',
        trigger_label_pt:
          'Resposta de emergência',
        trigger_label_en:
          'Emergency response',

        monitoring_code: 'continuous',
        monitoring_pt:
          'Monitorização contínua dos sinais vitais.',
        monitoring_en:
          'Continuous monitoring of vital signs.',

        response_pt:
          'Avaliação emergencial por equipe com competências em cuidados críticos e escalonamento conforme protocolo local.',
        response_en:
          'Emergency assessment by a team with critical-care competencies and escalation according to local policy.'
      };
    }


    if (total >= 5) {
      return {
        aggregate_band: 'medium',
        aggregate_label_pt:
          'Médio — total 5–6',
        aggregate_label_en:
          'Medium — total 5–6',

        trigger_code: 'medium',
        trigger_label_pt:
          'Resposta urgente',
        trigger_label_en:
          'Urgent response',

        monitoring_code:
          'minimum_hourly',

        monitoring_pt:
          'Monitorização no mínimo a cada 1 hora.',
        monitoring_en:
          'Monitoring at least hourly.',

        response_pt:
          'Solicitar avaliação clínica urgente conforme protocolo local.',
        response_en:
          'Request urgent clinical assessment according to local policy.'
      };
    }


    if (red) {
      return {
        aggregate_band: 'low',
        aggregate_label_pt:
          'Baixo — total 1–4',
        aggregate_label_en:
          'Low — total 1–4',

        trigger_code:
          'single_red',

        trigger_label_pt:
          'Parâmetro isolado com escore 3',
        trigger_label_en:
          'Single parameter score of 3',

        monitoring_code:
          'minimum_hourly',

        monitoring_pt:
          'Monitorização no mínimo a cada 1 hora.',
        monitoring_en:
          'Monitoring at least hourly.',

        response_pt:
          'Solicitar revisão clínica para determinar a necessidade de escalonamento.',
        response_en:
          'Request clinical review to determine whether escalation is required.'
      };
    }


    if (total >= 1) {
      return {
        aggregate_band: 'low',
        aggregate_label_pt:
          'Baixo — total 1–4',
        aggregate_label_en:
          'Low — total 1–4',

        trigger_code: 'low',
        trigger_label_pt: 'Baixo',
        trigger_label_en: 'Low',

        monitoring_code:
          'minimum_4_to_6_hourly',

        monitoring_pt:
          'Monitorização no mínimo a cada 4–6 horas.',
        monitoring_en:
          'Monitoring at least every 4–6 hours.',

        response_pt:
          'Avaliação clínica e decisão sobre frequência de observações ou escalonamento.',
        response_en:
          'Clinical assessment and decision on observation frequency or escalation.'
      };
    }


    return {
      aggregate_band: 'zero',

      aggregate_label_pt:
        'NEWS2 total 0',
      aggregate_label_en:
        'NEWS2 total 0',

      trigger_code: 'zero',

      trigger_label_pt:
        'Monitorização de rotina',
      trigger_label_en:
        'Routine monitoring',

      monitoring_code:
        'minimum_12_hourly',

      monitoring_pt:
        'Monitorização no mínimo a cada 12 horas.',
      monitoring_en:
        'Monitoring at least every 12 hours.',

      response_pt:
        'Manter monitorização NEWS2 conforme protocolo local.',
      response_en:
        'Continue NEWS2 monitoring according to local policy.'
    };
  }


  function calculateNews2(input) {
    const consciousnessValues =
      new Set([
        'alert',
        'new_confusion',
        'voice',
        'pain',
        'unresponsive'
      ]);


    const numericValues = [
      input.respiration_rate,
      input.spo2,
      input.systolic_bp,
      input.pulse,
      input.temperature
    ];


    if (
      !numericValues.every(Number.isFinite)
      || input.respiration_rate <= 0
      || input.spo2 < 1
      || input.spo2 > 100
      || input.systolic_bp <= 0
      || input.pulse <= 0
      || input.temperature < 20
      || input.temperature > 50
      || ![1, 2].includes(
        input.spo2_scale
      )
      || !consciousnessValues.has(
        input.consciousness
      )
    ) {
      throw new Error(
        'invalid_news2_input'
      );
    }


    if (
      input.spo2_scale === 2
      && !input.scale2_prescribed
    ) {
      throw new Error(
        'scale2_requires_prescribed_target'
      );
    }


    const components = {
      respiration_rate:
        respirationScore(
          input.respiration_rate
        ),

      spo2:
        input.spo2_scale === 1
          ? spo2Scale1Score(
              input.spo2
            )
          : spo2Scale2Score(
              input.spo2,
              input.supplemental_oxygen
            ),

      supplemental_oxygen:
        input.supplemental_oxygen
          ? 2
          : 0,

      systolic_bp:
        systolicScore(
          input.systolic_bp
        ),

      pulse:
        pulseScore(
          input.pulse
        ),

      consciousness:
        input.consciousness === 'alert'
          ? 0
          : 3,

      temperature:
        temperatureScore(
          input.temperature
        )
    };


    const total =
      Object.values(components)
        .reduce(
          (sum, value) => sum + value,
          0
        );


    const red =
      Object.entries(components)
        .some(
          ([key, value]) =>
            key !== 'supplemental_oxygen'
            && value === 3
        );


    return {
      tool: 'news2',

      total,
      components,

      spo2_scale:
        input.spo2_scale,

      scale2_prescribed:
        Boolean(
          input.scale2_prescribed
        ),

      supplemental_oxygen:
        Boolean(
          input.supplemental_oxygen
        ),

      single_parameter_red_score:
        red,

      clinical_judgement_note_pt:
        'O NEWS2 complementa, mas não substitui, o julgamento clínico.',

      clinical_judgement_note_en:
        'NEWS2 supplements, but does not replace, clinical judgement.',

      ...responseFor(
        total,
        red
      )
    };
  }



  const RENAL_FLOAT_ABS_TOL = 1e-9;


  function renalAtLeast(
    value,
    threshold
  ) {
    return (
      value > threshold
      || Math.abs(
        value - threshold
      ) <= RENAL_FLOAT_ABS_TOL
    );
  }


  function renalStrictlyBelow(
    value,
    threshold
  ) {
    return (
      value < threshold
      && Math.abs(
        value - threshold
      ) > RENAL_FLOAT_ABS_TOL
    );
  }


  function creatinineMgDl(
    value,
    unit
  ) {
    if (
      !Number.isFinite(value)
      || value <= 0
    ) {
      throw new Error(
        'invalid_creatinine'
      );
    }

    if (unit === 'mg/dL') {
      return value;
    }

    if (unit === 'umol/L') {
      return value / 88.4;
    }

    throw new Error(
      'unsupported_creatinine_unit'
    );
  }


  function gfrCategory(
    egfr
  ) {
    if (
      !Number.isFinite(egfr)
      || egfr < 0
    ) {
      throw new Error(
        'invalid_egfr'
      );
    }

    if (egfr >= 90) {
      return {
        code: 'G1',
        label_pt:
          'Normal ou elevada',
        label_en:
          'Normal or high'
      };
    }

    if (egfr >= 60) {
      return {
        code: 'G2',
        label_pt:
          'Levemente reduzida',
        label_en:
          'Mildly decreased'
      };
    }

    if (egfr >= 45) {
      return {
        code: 'G3a',
        label_pt:
          'Leve a moderadamente reduzida',
        label_en:
          'Mildly to moderately decreased'
      };
    }

    if (egfr >= 30) {
      return {
        code: 'G3b',
        label_pt:
          'Moderada a gravemente reduzida',
        label_en:
          'Moderately to severely decreased'
      };
    }

    if (egfr >= 15) {
      return {
        code: 'G4',
        label_pt:
          'Gravemente reduzida',
        label_en:
          'Severely decreased'
      };
    }

    return {
      code: 'G5',
      label_pt:
        'Falência renal',
      label_en:
        'Kidney failure'
    };
  }


  function albuminuriaCategory(
    acr,
    unit
  ) {
    if (
      !Number.isFinite(acr)
      || acr < 0
    ) {
      throw new Error(
        'invalid_acr'
      );
    }

    let code;

    if (unit === 'mg/g') {
      if (acr < 30) {
        code = 'A1';
      } else if (acr <= 300) {
        code = 'A2';
      } else {
        code = 'A3';
      }

    } else if (unit === 'mg/mmol') {
      if (acr < 3) {
        code = 'A1';
      } else if (acr <= 30) {
        code = 'A2';
      } else {
        code = 'A3';
      }

    } else {
      throw new Error(
        'unsupported_acr_unit'
      );
    }


    const labels = {
      A1: {
        pt:
          'Normal a levemente aumentada',
        en:
          'Normal to mildly increased'
      },

      A2: {
        pt:
          'Moderadamente aumentada',
        en:
          'Moderately increased'
      },

      A3: {
        pt:
          'Gravemente aumentada',
        en:
          'Severely increased'
      }
    };


    return {
      code,
      label_pt:
        labels[code].pt,
      label_en:
        labels[code].en
    };
  }


  function calculateEgfrCkdEpi2021(
    input
  ) {
    const {
      age_years,
      sex,
      serum_creatinine,
      creatinine_unit
    } = input;


    if (
      !Number.isInteger(age_years)
      || age_years < 18
      || age_years > 120
    ) {
      throw new Error(
        'adult_age_required'
      );
    }


    if (
      sex !== 'female'
      && sex !== 'male'
    ) {
      throw new Error(
        'invalid_sex'
      );
    }


    const scr =
      creatinineMgDl(
        serum_creatinine,
        creatinine_unit
      );


    let kappa;
    let alpha;
    let sexFactor;


    if (sex === 'female') {
      kappa = 0.7;
      alpha = -0.241;
      sexFactor = 1.012;
    } else {
      kappa = 0.9;
      alpha = -0.302;
      sexFactor = 1.0;
    }


    const ratio =
      scr / kappa;


    const egfr =
      142
      * Math.pow(
          Math.min(
            ratio,
            1.0
          ),
          alpha
        )
      * Math.pow(
          Math.max(
            ratio,
            1.0
          ),
          -1.200
        )
      * Math.pow(
          0.9938,
          age_years
        )
      * sexFactor;


    const category =
      gfrCategory(
        egfr
      );


    return {
      tool:
        'egfr_ckd_epi_2021',

      equation:
        'CKD-EPI creatinine 2021',

      race_coefficient_used:
        false,

      age_years,
      sex,

      creatinine_mg_dl:
        Math.round(
          scr * 10000
        ) / 10000,

      egfr_ml_min_1_73m2:
        Math.round(
          egfr * 10
        ) / 10,

      gfr_category:
        category.code,

      gfr_category_label_pt:
        category.label_pt,

      gfr_category_label_en:
        category.label_en,

      interpretation_pt:
        'TFG estimada indexada para 1,73 m². Não é equivalente ao clearance de creatinina de Cockcroft-Gault nem a uma TFG não indexada.',

      interpretation_en:
        'Estimated GFR indexed to 1.73 m². It is not equivalent to Cockcroft-Gault creatinine clearance or an unindexed GFR.'
    };
  }


  function classifyCkd(
    input
  ) {
    const {
      egfr_ml_min_1_73m2,
      acr = null,
      acr_unit = 'mg/g',
      chronicity_at_least_3_months = false,
      other_kidney_damage_marker = false
    } = input;


    if (
      !Number.isFinite(
        egfr_ml_min_1_73m2
      )
      || egfr_ml_min_1_73m2 < 0
    ) {
      throw new Error(
        'invalid_egfr'
      );
    }


    const g =
      gfrCategory(
        egfr_ml_min_1_73m2
      );


    let a = null;


    if (
      acr !== null
      && acr !== undefined
    ) {
      a = albuminuriaCategory(
        acr,
        acr_unit
      );
    }


    const reducedGfr =
      egfr_ml_min_1_73m2 < 60;


    const albuminuriaMarker =
      a !== null
      && (
        a.code === 'A2'
        || a.code === 'A3'
      );


    const abnormalityPresent =
      reducedGfr
      || albuminuriaMarker
      || Boolean(
        other_kidney_damage_marker
      );


    let statusCode;
    let statusPt;
    let statusEn;


    if (
      abnormalityPresent
      && chronicity_at_least_3_months
    ) {
      statusCode =
        'criteria_met';

      statusPt =
        'Os dados fornecidos atendem à definição de DRC quanto à cronicidade e aos marcadores informados.';

      statusEn =
        'The supplied data meet the CKD definition with respect to the reported chronicity and kidney abnormality markers.';

    } else if (
      abnormalityPresent
    ) {
      statusCode =
        'chronicity_not_established';

      statusPt =
        'Há marcador compatível com doença renal, mas a cronicidade mínima de 3 meses não foi confirmada; DRC não deve ser inferida deste resultado isolado.';

      statusEn =
        'A kidney abnormality marker is present, but the minimum 3-month chronicity has not been confirmed; CKD must not be inferred from this isolated result.';

    } else {
      statusCode =
        'criteria_not_met_by_supplied_data';

      statusPt =
        'Os dados fornecidos não atendem, por si só, à definição de DRC.';

      statusEn =
        'The supplied data do not, by themselves, meet the definition of CKD.';
    }


    return {
      tool:
        'ckd_classification',

      gfr_category:
        g.code,

      gfr_category_label_pt:
        g.label_pt,

      gfr_category_label_en:
        g.label_en,

      albuminuria_category:
        a?.code ?? null,

      albuminuria_category_label_pt:
        a?.label_pt ?? null,

      albuminuria_category_label_en:
        a?.label_en ?? null,

      ga_classification:
        a
          ? `${g.code}/${a.code}`
          : g.code,

      chronicity_at_least_3_months:
        Boolean(
          chronicity_at_least_3_months
        ),

      other_kidney_damage_marker:
        Boolean(
          other_kidney_damage_marker
        ),

      ckd_status_code:
        statusCode,

      ckd_status_pt:
        statusPt,

      ckd_status_en:
        statusEn,

      classification_note_pt:
        'A classificação completa KDIGO é CGA (causa, categoria G e categoria A). Este módulo determina G/A; a causa não é inferida automaticamente.',

      classification_note_en:
        'Complete KDIGO classification is CGA (cause, G category and A category). This module determines G/A; cause is not inferred automatically.'
    };
  }


  const AKI_CRITERIA_PT = {
    creatinine_delta_0_3_within_48h:
      'Aumento de creatinina ≥0,3 mg/dL em até 48 horas.',

    creatinine_ratio_1_5_within_7d:
      'Creatinina ≥1,5 vez o basal em até 7 dias.',

    creatinine_ratio_2_0_to_2_9:
      'Creatinina entre 2,0 e 2,9 vezes o basal.',

    creatinine_ratio_3_0:
      'Creatinina ≥3,0 vezes o basal.',

    creatinine_to_4_0:
      'Aumento agudo da creatinina para ≥4,0 mg/dL.',

    urine_output_below_0_5_6h:
      'Diurese <0,5 mL/kg/h por pelo menos 6 horas.',

    urine_output_below_0_5_12h:
      'Diurese <0,5 mL/kg/h por pelo menos 12 horas.',

    urine_output_below_0_3_24h:
      'Diurese <0,3 mL/kg/h por pelo menos 24 horas.',

    anuria_6h:
      'Anúria por pelo menos 6 horas.',

    anuria_12h:
      'Anúria por pelo menos 12 horas.',

    renal_replacement_therapy:
      'Terapia renal substitutiva iniciada.'
  };


  const AKI_CRITERIA_EN = {
    creatinine_delta_0_3_within_48h:
      'Serum creatinine increased by ≥0.3 mg/dL within 48 hours.',

    creatinine_ratio_1_5_within_7d:
      'Serum creatinine is ≥1.5 times baseline within 7 days.',

    creatinine_ratio_2_0_to_2_9:
      'Serum creatinine is 2.0–2.9 times baseline.',

    creatinine_ratio_3_0:
      'Serum creatinine is ≥3.0 times baseline.',

    creatinine_to_4_0:
      'Acute serum creatinine increase to ≥4.0 mg/dL.',

    urine_output_below_0_5_6h:
      'Urine output <0.5 mL/kg/h for at least 6 hours.',

    urine_output_below_0_5_12h:
      'Urine output <0.5 mL/kg/h for at least 12 hours.',

    urine_output_below_0_3_24h:
      'Urine output <0.3 mL/kg/h for at least 24 hours.',

    anuria_6h:
      'Anuria for at least 6 hours.',

    anuria_12h:
      'Anuria for at least 12 hours.',

    renal_replacement_therapy:
      'Kidney replacement therapy initiated.'
  };


  function calculateKdigoAki(
    input
  ) {
    const hasCurrentCreatinine =
      input.current_creatinine !== null
      && input.current_creatinine !== undefined;


    const current =
      hasCurrentCreatinine
        ? creatinineMgDl(
            input.current_creatinine,
            input.current_creatinine_unit
          )
        : null;


    const criteriaCodes = [];

    let creatinineStage = null;
    let urineStage = null;
    let rrtStage = null;

    let creatinineRatio = null;
    let creatinineDelta = null;
    let urineRate = null;


    if (
      input.baseline_creatinine !== null
      && input.baseline_creatinine !== undefined
    ) {
      if (current === null) {
        throw new Error(
          'current_creatinine_required_with_baseline'
        );
      }


      if (
        input.baseline_interval_hours === null
        || input.baseline_interval_hours === undefined
      ) {
        throw new Error(
          'baseline_interval_required'
        );
      }


      if (
        !Number.isFinite(
          input.baseline_interval_hours
        )
        || input.baseline_interval_hours < 0
      ) {
        throw new Error(
          'invalid_baseline_interval'
        );
      }


      const baseline =
        creatinineMgDl(
          input.baseline_creatinine,
          input.baseline_creatinine_unit
            || input.current_creatinine_unit
        );


      creatinineRatio =
        current / baseline;

      creatinineDelta =
        current - baseline;


      if (
        input.baseline_interval_hours <= 168
      ) {
        const acuteByRatio =
          renalAtLeast(
            creatinineRatio,
            1.5
          );


        const acuteByDelta =
          input.baseline_interval_hours <= 48
          && renalAtLeast(
            creatinineDelta,
            0.3
          );


        const acuteCreatinine =
          acuteByRatio
          || acuteByDelta;


        if (acuteByDelta) {
          criteriaCodes.push(
            'creatinine_delta_0_3_within_48h'
          );
        }


        if (acuteByRatio) {
          criteriaCodes.push(
            'creatinine_ratio_1_5_within_7d'
          );
        }


        if (acuteCreatinine) {
          if (
            renalAtLeast(
              creatinineRatio,
              3.0
            )
            || renalAtLeast(
              current,
              4.0
            )
          ) {
            creatinineStage = 3;


            if (
              renalAtLeast(
                creatinineRatio,
                3.0
              )
            ) {
              criteriaCodes.push(
                'creatinine_ratio_3_0'
              );
            }


            if (
              renalAtLeast(
                current,
                4.0
              )
            ) {
              criteriaCodes.push(
                'creatinine_to_4_0'
              );
            }

          } else if (
            renalAtLeast(
              creatinineRatio,
              2.0
            )
          ) {
            creatinineStage = 2;

            criteriaCodes.push(
              'creatinine_ratio_2_0_to_2_9'
            );

          } else {
            creatinineStage = 1;
          }

        } else {
          creatinineStage = 0;
        }
      }
    }


    const urineFields = [
      input.weight_kg,
      input.urine_output_ml,
      input.urine_output_duration_hours
    ];


    const suppliedUrineFields =
      urineFields.filter(
        value =>
          value !== null
          && value !== undefined
      ).length;


    if (
      suppliedUrineFields !== 0
      && suppliedUrineFields !== 3
    ) {
      throw new Error(
        'partial_urine_output_data'
      );
    }


    if (suppliedUrineFields === 3) {
      const weight =
        input.weight_kg;

      const urine =
        input.urine_output_ml;

      const duration =
        input.urine_output_duration_hours;


      if (
        !Number.isFinite(weight)
        || weight <= 0
        || !Number.isFinite(urine)
        || urine < 0
        || !Number.isFinite(duration)
        || duration <= 0
      ) {
        throw new Error(
          'invalid_urine_output_data'
        );
      }


      urineRate =
        urine
        / weight
        / duration;


      if (
        duration >= 24
        && renalStrictlyBelow(
          urineRate,
          0.3
        )
      ) {
        urineStage = 3;

        criteriaCodes.push(
          'urine_output_below_0_3_24h'
        );

      } else if (
        duration >= 12
        && renalStrictlyBelow(
          urineRate,
          0.5
        )
      ) {
        urineStage = 2;

        criteriaCodes.push(
          'urine_output_below_0_5_12h'
        );

      } else if (
        duration >= 6
        && renalStrictlyBelow(
          urineRate,
          0.5
        )
      ) {
        urineStage = 1;

        criteriaCodes.push(
          'urine_output_below_0_5_6h'
        );

      } else {
        urineStage = 0;
      }
    }


    if (
      input.anuria_duration_hours !== null
      && input.anuria_duration_hours !== undefined
    ) {
      const duration =
        input.anuria_duration_hours;


      if (
        !Number.isFinite(duration)
        || duration < 0
      ) {
        throw new Error(
          'invalid_anuria_duration'
        );
      }


      let anuriaStage = 0;


      if (duration >= 12) {
        anuriaStage = 3;

        criteriaCodes.push(
          'anuria_12h'
        );

      } else if (duration >= 6) {
        anuriaStage = 1;

        criteriaCodes.push(
          'anuria_6h'
        );
      }


      urineStage =
        Math.max(
          urineStage ?? 0,
          anuriaStage
        );
    }


    if (
      input.renal_replacement_therapy
    ) {
      rrtStage = 3;

      criteriaCodes.push(
        'renal_replacement_therapy'
      );
    }


    const evaluableStages = [
      creatinineStage,
      urineStage,
      rrtStage
    ].filter(
      value =>
        value !== null
        && value !== undefined
    );


    let stage;
    let evaluable;
    let akiCriteriaMet;
    let interpretationPt;
    let interpretationEn;


    if (
      evaluableStages.length === 0
    ) {
      stage = null;
      evaluable = false;
      akiCriteriaMet = null;

      interpretationPt =
        'Dados insuficientes para determinar estágio KDIGO de LRA. É necessário um critério temporal de creatinina, diurese mensurável ou informação sobre terapia renal substitutiva.';

      interpretationEn =
        'Insufficient data to determine KDIGO AKI stage. A time-qualified creatinine comparison, measured urine output or kidney replacement therapy information is required.';

    } else {
      stage =
        Math.max(
          ...evaluableStages
        );

      evaluable = true;

      akiCriteriaMet =
        stage > 0;


      if (stage === 0) {
        interpretationPt =
          'Nenhum critério KDIGO de LRA foi atendido pelos dados temporais fornecidos.';

        interpretationEn =
          'No KDIGO AKI criterion was met by the time-qualified data supplied.';

      } else {
        interpretationPt =
          `LRA KDIGO estágio ${stage} pelos critérios fornecidos. O estágio final corresponde ao critério de maior gravidade.`;

        interpretationEn =
          `KDIGO AKI stage ${stage} by the supplied criteria. The final stage is determined by the most severe qualifying criterion.`;
      }
    }


    const uniqueCodes = [
      ...new Set(
        criteriaCodes
      )
    ];


    return {
      tool: 'kdigo_aki',

      evaluable,
      aki_criteria_met:
        akiCriteriaMet,

      stage,

      creatinine_stage:
        creatinineStage,

      urine_output_stage:
        urineStage,

      rrt_stage:
        rrtStage,

      current_creatinine_mg_dl:
        current === null
          ? null
          : Math.round(
              current * 10000
            ) / 10000,

      creatinine_ratio:
        creatinineRatio === null
          ? null
          : Math.round(
              creatinineRatio * 10000
            ) / 10000,

      creatinine_delta_mg_dl:
        creatinineDelta === null
          ? null
          : Math.round(
              creatinineDelta * 10000
            ) / 10000,

      urine_output_ml_kg_h:
        urineRate === null
          ? null
          : Math.round(
              urineRate * 10000
            ) / 10000,

      criteria_codes:
        uniqueCodes,

      criteria_pt:
        uniqueCodes.map(
          code =>
            AKI_CRITERIA_PT[code]
        ),

      criteria_en:
        uniqueCodes.map(
          code =>
            AKI_CRITERIA_EN[code]
        ),

      interpretation_pt:
        interpretationPt,

      interpretation_en:
        interpretationEn
    };
  }



  function calculateHemodynamics(
    input
  ) {
    const systolic =
      input.systolic_bp;

    const diastolic =
      input.diastolic_bp;

    const heartRate =
      input.heart_rate;


    if (
      !Number.isFinite(systolic)
      || systolic <= 0
      || !Number.isFinite(diastolic)
      || diastolic <= 0
      || !Number.isFinite(heartRate)
      || heartRate <= 0
    ) {
      throw new Error(
        'invalid_hemodynamic_input'
      );
    }


    if (
      systolic < diastolic
    ) {
      throw new Error(
        'systolic_below_diastolic'
      );
    }


    const pulsePressure =
      systolic
      - diastolic;


    const map =
      diastolic
      + pulsePressure / 3;


    const shockIndex =
      heartRate
      / systolic;


    const modifiedShockIndex =
      heartRate
      / map;


    return {
      tool:
        'hemodynamics',

      systolic_bp_mm_hg:
        Math.round(
          systolic * 10
        ) / 10,

      diastolic_bp_mm_hg:
        Math.round(
          diastolic * 10
        ) / 10,

      heart_rate_bpm:
        Math.round(
          heartRate * 10
        ) / 10,

      pulse_pressure_mm_hg:
        Math.round(
          pulsePressure * 10
        ) / 10,

      mean_arterial_pressure_mm_hg:
        Math.round(
          map * 10
        ) / 10,

      shock_index:
        Math.round(
          shockIndex * 1000
        ) / 1000,

      modified_shock_index:
        Math.round(
          modifiedShockIndex * 1000
        ) / 1000,

      map_method:
        'DBP + 1/3(SBP - DBP)',

      pulse_pressure_method:
        'SBP - DBP',

      shock_index_method:
        'HR / SBP',

      modified_shock_index_method:
        'HR / MAP',

      threshold_classification_applied:
        false,

      interpretation_pt:
        'Os índices são auxiliares de avaliação hemodinâmica e devem ser interpretados junto ao contexto clínico, tendência dos sinais vitais, perfusão e comorbidades. Não foi aplicado um ponto de corte universal para Shock Index ou Modified Shock Index.',

      interpretation_en:
        'These indices are adjuncts to haemodynamic assessment and should be interpreted with the clinical context, vital-sign trends, perfusion and comorbidities. No universal Shock Index or Modified Shock Index cut-off has been applied.',

      map_note_pt:
        'A PAM calculada é uma aproximação baseada em PAS/PAD e não substitui a PAM derivada diretamente da curva arterial quando esta estiver disponível.',

      map_note_en:
        'Calculated MAP is an approximation derived from SBP/DBP and does not replace MAP obtained directly from an arterial waveform when available.'
    };
  }


  globalThis.ClinicalTools =
    Object.freeze({
      calculateNews2,
      calculateEgfrCkdEpi2021,
      classifyCkd,
      calculateKdigoAki,
      calculateHemodynamics
    });
})();
