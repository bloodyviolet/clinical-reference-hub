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


  function classifyBrazilPcdtCkdContext(
    input
  ) {
    const egfr =
      input.egfr_ml_min_1_73m2;

    const acr =
      input.acr ?? null;

    const acrUnit =
      input.acr_unit ?? 'mg/g';

    const chronicity =
      Boolean(
        input.chronicity_at_least_3_months
      );

    const otherMarker =
      Boolean(
        input.other_kidney_damage_marker
      );

    const onDialysis =
      Boolean(
        input.on_dialysis
      );


    if (
      !Number.isFinite(egfr)
      || egfr < 0
    ) {
      throw new Error(
        'invalid_egfr'
      );
    }


    if (
      acr !== null
      && (
        !Number.isFinite(acr)
        || acr < 0
      )
    ) {
      throw new Error(
        'invalid_acr'
      );
    }


    let albuminuriaMarker = false;


    if (acr !== null) {
      const internationalAcr =
        albuminuriaCategory(
          acr,
          acrUnit
        );

      albuminuriaMarker =
        internationalAcr.code === 'A2'
        || internationalAcr.code === 'A3';
    }


    const kidneyDamageMarker =
      albuminuriaMarker
      || otherMarker;


    let pcdtAcrCategory = null;
    let pcdtAcrEvaluable = false;
    let pcdtAcrAmbiguous300 = false;
    let pcdtAcrNotePt;
    let pcdtAcrNoteEn;


    if (acr === null) {
      pcdtAcrNotePt =
        'RAC não informada; categoria A do PCDT não avaliada.';

      pcdtAcrNoteEn =
        'ACR not supplied; PCDT A category not assessed.';

    } else if (acrUnit !== 'mg/g') {
      pcdtAcrNotePt =
        'A tabela nacional auditada do PCDT foi transcrita em mg/g. A categoria A do PCDT não é convertida automaticamente a partir de mg/mmol.';

      pcdtAcrNoteEn =
        'The audited national PCDT table is expressed in mg/g. The PCDT A category is not automatically converted from mg/mmol.';

    } else if (
      Math.abs(
        acr - 300
      ) <= RENAL_FLOAT_ABS_TOL
    ) {
      pcdtAcrAmbiguous300 = true;

      pcdtAcrNotePt =
        'O PCDT vigente apresenta A2 como 30–299 mg/g e A3 como >300 mg/g, deixando exatamente 300 mg/g textualmente sem categoria. O sistema não infere uma categoria nacional.';

      pcdtAcrNoteEn =
        'The current PCDT renders A2 as 30–299 mg/g and A3 as >300 mg/g, leaving exactly 300 mg/g textually unassigned. No national category is inferred.';

    } else {
      pcdtAcrEvaluable = true;

      if (acr < 30) {
        pcdtAcrCategory = 'A1';

      } else if (acr < 300) {
        pcdtAcrCategory = 'A2';

      } else {
        pcdtAcrCategory = 'A3';
      }

      pcdtAcrNotePt =
        'Categoria RAC conforme a tabela nacional do PCDT vigente.';

      pcdtAcrNoteEn =
        'ACR category according to the current national PCDT table.';
    }


    let stage = null;
    let stageRequiresDamageMarker = false;


    if (egfr < 15) {
      stage =
        onDialysis
          ? '5D'
          : '5';

    } else if (egfr < 30) {
      stage = '4';

    } else if (egfr < 45) {
      stage = '3B';

    } else if (egfr < 60) {
      stage = '3A';

    } else if (egfr < 90) {
      stageRequiresDamageMarker = true;

      if (kidneyDamageMarker) {
        stage = '2';
      }

    } else {
      stageRequiresDamageMarker = true;

      if (kidneyDamageMarker) {
        stage = '1';
      }
    }


    const stageLabels = {
      '1': {
        pt: 'Estágio 1',
        en: 'Stage 1'
      },
      '2': {
        pt: 'Estágio 2',
        en: 'Stage 2'
      },
      '3A': {
        pt: 'Estágio 3A',
        en: 'Stage 3A'
      },
      '3B': {
        pt: 'Estágio 3B',
        en: 'Stage 3B'
      },
      '4': {
        pt: 'Estágio 4',
        en: 'Stage 4'
      },
      '5': {
        pt: 'Estágio 5',
        en: 'Stage 5'
      },
      '5D': {
        pt: 'Estágio 5D · em diálise',
        en: 'Stage 5D · on dialysis'
      }
    };


    let stageLabelPt = null;
    let stageLabelEn = null;
    let stageNotePt;
    let stageNoteEn;


    if (stage === null) {
      stageNotePt =
        'Para TFGe ≥60 mL/min/1,73 m², o PCDT exige marcador de dano renal para atribuir estágio 1 ou 2; nenhum marcador suficiente foi informado.';

      stageNoteEn =
        'For eGFR ≥60 mL/min/1.73 m², the PCDT requires a kidney-damage marker to assign stage 1 or 2; no sufficient marker was supplied.';

    } else {
      stageLabelPt =
        stageLabels[stage].pt;

      stageLabelEn =
        stageLabels[stage].en;

      stageNotePt =
        'Estágio contextual conforme o PCDT nacional. Não representa recálculo da TFGe pela equação impressa no PCDT.';

      stageNoteEn =
        'Contextual stage according to the national PCDT. This does not recalculate eGFR using the equation printed in the PCDT.';
    }


    const abnormalityPresent =
      egfr < 60
      || kidneyDamageMarker;


    let statusCode;
    let statusPt;
    let statusEn;


    if (
      abnormalityPresent
      && chronicity
    ) {
      statusCode =
        'criteria_met';

      statusPt =
        'Os dados fornecidos são compatíveis com os critérios de DRC do PCDT quanto à anormalidade renal e à cronicidade informada.';

      statusEn =
        'The supplied data are compatible with the PCDT CKD criteria regarding kidney abnormality and reported chronicity.';

    } else if (
      abnormalityPresent
    ) {
      statusCode =
        'chronicity_not_established';

      statusPt =
        'Há anormalidade renal compatível, mas a cronicidade mínima de 3 meses não foi confirmada.';

      statusEn =
        'A compatible kidney abnormality is present, but the minimum 3-month chronicity has not been confirmed.';

    } else {
      statusCode =
        'criteria_not_met_by_supplied_data';

      statusPt =
        'Os dados fornecidos não estabelecem DRC pelo PCDT nacional.';

      statusEn =
        'The supplied data do not establish CKD under the national PCDT.';
    }


    return {
      pcdt_stage:
        stage,

      pcdt_stage_label_pt:
        stageLabelPt,

      pcdt_stage_label_en:
        stageLabelEn,

      pcdt_stage_requires_damage_marker:
        stageRequiresDamageMarker,

      pcdt_stage_note_pt:
        stageNotePt,

      pcdt_stage_note_en:
        stageNoteEn,

      kidney_damage_marker_present:
        kidneyDamageMarker,

      pcdt_acr_category:
        pcdtAcrCategory,

      pcdt_acr_category_evaluable:
        pcdtAcrEvaluable,

      pcdt_acr_exact_300_ambiguous:
        pcdtAcrAmbiguous300,

      pcdt_acr_note_pt:
        pcdtAcrNotePt,

      pcdt_acr_note_en:
        pcdtAcrNoteEn,

      pcdt_ckd_status_code:
        statusCode,

      pcdt_ckd_status_pt:
        statusPt,

      pcdt_ckd_status_en:
        statusEn,

      pcdt_equation_calculation_applied:
        false,

      pcdt_equation_status:
        'not_implemented_due_verified_source_conflict',

      race_or_ancestry_input_used:
        false,

      source_version:
        'PCDT DRC 2024; annex updated 2025-02-07'
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
      other_kidney_damage_marker = false,
      on_dialysis = false
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


    const brazilPcdtContext =
      classifyBrazilPcdtCkdContext({
        egfr_ml_min_1_73m2,
        acr,
        acr_unit,
        chronicity_at_least_3_months,
        other_kidney_damage_marker,
        on_dialysis
      });


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

      on_dialysis:
        Boolean(
          on_dialysis
        ),

      brazil_pcdt_context:
        brazilPcdtContext,

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



  function calculateOxygenation(
    input
  ) {
    const fio2Percent =
      input.fio2_percent;

    const pao2 =
      input.pao2_mm_hg;

    const spo2 =
      input.spo2_percent;


    if (
      !Number.isFinite(fio2Percent)
      || fio2Percent < 21
      || fio2Percent > 100
    ) {
      throw new Error(
        'invalid_fio2'
      );
    }


    const hasPao2 =
      pao2 !== null
      && pao2 !== undefined;


    const hasSpo2 =
      spo2 !== null
      && spo2 !== undefined;


    if (
      !hasPao2
      && !hasSpo2
    ) {
      throw new Error(
        'oxygenation_measurement_required'
      );
    }


    if (
      hasPao2
      && (
        !Number.isFinite(pao2)
        || pao2 <= 0
      )
    ) {
      throw new Error(
        'invalid_pao2'
      );
    }


    if (
      hasSpo2
      && (
        !Number.isFinite(spo2)
        || spo2 < 1
        || spo2 > 100
      )
    ) {
      throw new Error(
        'invalid_spo2'
      );
    }


    const fio2Fraction =
      fio2Percent / 100;


    const pfRatio =
      hasPao2
        ? pao2 / fio2Fraction
        : null;


    const sfRatio =
      hasSpo2
        ? spo2 / fio2Fraction
        : null;


    const sfAbove97 =
      hasSpo2
        ? spo2 > 97
        : null;


    const sfThresholdApplicable =
      hasSpo2
        ? spo2 <= 97
        : null;


    return {
      tool:
        'oxygenation_ratios',

      fio2_percent:
        Math.round(
          fio2Percent * 10
        ) / 10,

      fio2_fraction:
        Math.round(
          fio2Fraction * 10000
        ) / 10000,

      pao2_mm_hg:
        hasPao2
          ? Math.round(
              pao2 * 10
            ) / 10
          : null,

      spo2_percent:
        hasSpo2
          ? Math.round(
              spo2 * 10
            ) / 10
          : null,

      pf_ratio_mm_hg:
        pfRatio === null
          ? null
          : Math.round(
              pfRatio * 10
            ) / 10,

      sf_ratio:
        sfRatio === null
          ? null
          : Math.round(
              sfRatio * 10
            ) / 10,

      pf_method:
        'PaO2 / FiO2 fraction',

      sf_method:
        'SpO2 / FiO2 fraction',

      ards_classification_applied:
        false,

      sf_spo2_above_97_caution:
        sfAbove97,

      global_ards_sf_threshold_applicable:
        sfThresholdApplicable,

      interpretation_pt:
        'As relações P/F e S/F quantificam oxigenação, mas não estabelecem diagnóstico nem gravidade de SDRA isoladamente. A interpretação exige contexto clínico, suporte respiratório e os demais critérios da definição aplicável.',

      interpretation_en:
        'P/F and S/F ratios quantify oxygenation but do not independently establish an ARDS diagnosis or severity. Interpretation requires clinical context, respiratory support and the other criteria of the applicable definition.',

      sf_note_pt:
        !hasSpo2
          ? null
          : sfAbove97
            ? 'SpO2 acima de 97% reduz a utilidade discriminativa da relação S/F; o limiar S/F da definição global de SDRA não deve ser aplicado neste valor.'
            : 'Quando usada na definição global de SDRA, a relação S/F é considerada com SpO2 ≤97%; a relação isolada não confirma SDRA.',

      sf_note_en:
        !hasSpo2
          ? null
          : sfAbove97
            ? 'SpO2 above 97% reduces the discriminatory utility of the S/F ratio; the Global ARDS S/F threshold should not be applied to this value.'
            : 'When used in the Global ARDS definition, the S/F ratio is considered with SpO2 ≤97%; the ratio alone does not confirm ARDS.',

      fio2_note_pt:
        'A FiO2 foi informada explicitamente. Este módulo não estima FiO2 a partir de fluxo de oxigênio ou do tipo de dispositivo.',

      fio2_note_en:
        'FiO2 was supplied explicitly. This module does not estimate FiO2 from oxygen flow rate or delivery-device type.'
    };
  }



  const METABOLIC_FLOAT_ABS_TOL =
    1e-9;


  function metabolicStrictlyAbove(
    value,
    threshold
  ) {
    return (
      value > threshold
      && Math.abs(
        value - threshold
      ) > METABOLIC_FLOAT_ABS_TOL
    );
  }


  function metabolicStrictlyBelow(
    value,
    threshold
  ) {
    return (
      value < threshold
      && Math.abs(
        value - threshold
      ) > METABOLIC_FLOAT_ABS_TOL
    );
  }


  function calculateMetabolicToolkit(
    input
  ) {
    const sodium =
      input.sodium_meq_l;

    const chloride =
      input.chloride_meq_l;

    const bicarbonate =
      input.bicarbonate_meq_l;

    const albumin =
      input.albumin_g_dl;

    const glucose =
      input.glucose_mg_dl;

    const bun =
      input.bun_mg_dl;

    const paco2 =
      input.paco2_mm_hg;

    const confirmed =
      Boolean(
        input.metabolic_acidosis_confirmed
      );


    if (
      !Number.isFinite(sodium)
      || sodium <= 0
    ) {
      throw new Error(
        'invalid_sodium'
      );
    }


    const hasChloride =
      chloride !== null
      && chloride !== undefined;

    const hasBicarbonate =
      bicarbonate !== null
      && bicarbonate !== undefined;


    if (
      hasChloride
      !== hasBicarbonate
    ) {
      throw new Error(
        'chloride_bicarbonate_required_together'
      );
    }


    if (
      hasChloride
      && (
        !Number.isFinite(chloride)
        || chloride <= 0
      )
    ) {
      throw new Error(
        'invalid_chloride'
      );
    }


    if (
      hasBicarbonate
      && (
        !Number.isFinite(bicarbonate)
        || bicarbonate <= 0
      )
    ) {
      throw new Error(
        'invalid_bicarbonate'
      );
    }


    const hasAlbumin =
      albumin !== null
      && albumin !== undefined;


    if (hasAlbumin) {
      if (
        !Number.isFinite(albumin)
        || albumin <= 0
      ) {
        throw new Error(
          'invalid_albumin'
        );
      }

      if (!hasChloride) {
        throw new Error(
          'albumin_requires_anion_gap_inputs'
        );
      }
    }


    const hasGlucose =
      glucose !== null
      && glucose !== undefined;


    if (
      hasGlucose
      && (
        !Number.isFinite(glucose)
        || glucose < 0
      )
    ) {
      throw new Error(
        'invalid_glucose'
      );
    }


    const hasBun =
      bun !== null
      && bun !== undefined;


    if (hasBun) {
      if (
        !Number.isFinite(bun)
        || bun < 0
      ) {
        throw new Error(
          'invalid_bun'
        );
      }

      if (!hasGlucose) {
        throw new Error(
          'bun_requires_glucose'
        );
      }
    }


    const hasPaco2 =
      paco2 !== null
      && paco2 !== undefined;


    if (
      hasPaco2
      && (
        !Number.isFinite(paco2)
        || paco2 <= 0
      )
    ) {
      throw new Error(
        'invalid_paco2'
      );
    }


    if (
      !hasChloride
      && !hasGlucose
    ) {
      throw new Error(
        'metabolic_calculation_input_required'
      );
    }


    let anionGap = null;
    let correctedAg = null;


    if (hasChloride) {
      anionGap =
        sodium
        - chloride
        - bicarbonate;


      if (hasAlbumin) {
        correctedAg =
          anionGap
          + 2.5
          * (
            4.0
            - albumin
          );
      }
    }


    let correctedSodium = null;
    let sodiumDelta = null;


    if (hasGlucose) {
      const excess =
        Math.max(
          glucose - 100,
          0
        );

      sodiumDelta =
        1.6
        * excess
        / 100;

      correctedSodium =
        sodium
        + sodiumDelta;
    }


    let osmolality = null;


    if (
      hasGlucose
      && hasBun
    ) {
      osmolality =
        2 * sodium
        + glucose / 18
        + bun / 2.8;
    }


    const metabolicAcidosisGate =
      confirmed
      && hasBicarbonate
      && metabolicStrictlyBelow(
        bicarbonate,
        24
      );


    let winterExpected = null;
    let winterLower = null;
    let winterUpper = null;
    let winterStatus = null;
    let winterPt = null;
    let winterEn = null;


    if (metabolicAcidosisGate) {
      winterExpected =
        1.5 * bicarbonate
        + 8;

      winterLower =
        winterExpected - 2;

      winterUpper =
        winterExpected + 2;


      if (hasPaco2) {
        if (
          metabolicStrictlyAbove(
            paco2,
            winterUpper
          )
        ) {
          winterStatus =
            'paco2_above_expected';

          winterPt =
            'PaCO2 acima da faixa esperada pela fórmula de Winter; isso sugere componente adicional de acidose respiratória.';

          winterEn =
            'PaCO2 is above the Winter expected range; this suggests an additional respiratory acidosis component.';

        } else if (
          metabolicStrictlyBelow(
            paco2,
            winterLower
          )
        ) {
          winterStatus =
            'paco2_below_expected';

          winterPt =
            'PaCO2 abaixo da faixa esperada pela fórmula de Winter; isso sugere componente adicional de alcalose respiratória.';

          winterEn =
            'PaCO2 is below the Winter expected range; this suggests an additional respiratory alkalosis component.';

        } else {
          winterStatus =
            'within_expected';

          winterPt =
            'PaCO2 dentro da faixa esperada pela fórmula de Winter para compensação respiratória.';

          winterEn =
            'PaCO2 is within the Winter expected range for respiratory compensation.';
        }
      }
    }


    const agForDelta =
      correctedAg !== null
        ? correctedAg
        : anionGap;


    let deltaRatio = null;
    let deltaApplied = false;
    let deltaBasis = null;
    let deltaCode = null;
    let deltaPt = null;
    let deltaEn = null;


    const deltaGate =
      metabolicAcidosisGate
      && agForDelta !== null
      && metabolicStrictlyAbove(
        agForDelta,
        12
      );


    if (deltaGate) {
      const denominator =
        24 - bicarbonate;


      if (
        metabolicStrictlyAbove(
          denominator,
          0
        )
      ) {
        deltaRatio =
          (
            agForDelta - 12
          )
          / denominator;

        deltaApplied = true;

        deltaBasis =
          correctedAg !== null
            ? 'albumin_corrected'
            : 'uncorrected';


        if (
          metabolicStrictlyBelow(
            deltaRatio,
            1
          )
        ) {
          deltaCode =
            'suggests_additional_nagma';

          deltaPt =
            'Delta ratio <1 sugere componente adicional de acidose metabólica com ânion gap normal.';

          deltaEn =
            'Delta ratio <1 suggests an additional normal-anion-gap metabolic acidosis.';

        } else if (
          metabolicStrictlyAbove(
            deltaRatio,
            2
          )
        ) {
          deltaCode =
            'suggests_additional_metabolic_alkalosis';

          deltaPt =
            'Delta ratio >2 sugere alcalose metabólica adicional ou bicarbonato basal previamente elevado.';

          deltaEn =
            'Delta ratio >2 suggests additional metabolic alkalosis or a previously elevated baseline bicarbonate.';

        } else {
          deltaCode =
            'compatible_with_predominant_hagma';

          deltaPt =
            'Delta ratio entre 1 e 2 é compatível com acidose metabólica de ânion gap elevado predominante, sem excluir outros processos.';

          deltaEn =
            'A delta ratio between 1 and 2 is compatible with predominant high-anion-gap metabolic acidosis, without excluding other processes.';
        }
      }
    }


    const validityPt = [];
    const validityEn = [];


    if (!confirmed) {
      validityPt.push(
        'Compensação pela fórmula de Winter e delta ratio não foram interpretados porque acidose metabólica não foi confirmada explicitamente.'
      );

      validityEn.push(
        'Winter compensation and delta-ratio interpretation were not applied because metabolic acidosis was not explicitly confirmed.'
      );

    } else if (
      !metabolicAcidosisGate
    ) {
      validityPt.push(
        'A análise de compensação/delta não foi aplicada porque o bicarbonato informado não estava abaixo de 24 mEq/L ou estava ausente.'
      );

      validityEn.push(
        'Compensation/delta analysis was not applied because the supplied bicarbonate was not below 24 mEq/L or was unavailable.'
      );

    } else if (
      !deltaApplied
    ) {
      validityPt.push(
        'O delta ratio não foi aplicado porque o ânion gap utilizado não excedeu 12 mEq/L.'
      );

      validityEn.push(
        'The delta ratio was not applied because the selected anion gap did not exceed 12 mEq/L.'
      );
    }


    if (
      !hasAlbumin
      && anionGap !== null
    ) {
      validityPt.push(
        'Ânion gap não corrigido por albumina; valores de referência também dependem do método/laboratório.'
      );

      validityEn.push(
        'Anion gap was not albumin-corrected; reference intervals also depend on laboratory methodology.'
      );
    }


    if (hasGlucose) {
      validityPt.push(
        'Sódio corrigido usa a convenção de +1,6 mEq/L por 100 mg/dL de glicose acima de 100 mg/dL.'
      );

      validityEn.push(
        'Corrected sodium uses the +1.6 mEq/L per 100 mg/dL glucose above 100 mg/dL convention.'
      );
    }


    return {
      tool:
        'acid_base_metabolic',

      sodium_meq_l:
        Math.round(
          sodium * 10
        ) / 10,

      chloride_meq_l:
        hasChloride
          ? Math.round(
              chloride * 10
            ) / 10
          : null,

      bicarbonate_meq_l:
        hasBicarbonate
          ? Math.round(
              bicarbonate * 10
            ) / 10
          : null,

      albumin_g_dl:
        hasAlbumin
          ? Math.round(
              albumin * 100
            ) / 100
          : null,

      glucose_mg_dl:
        hasGlucose
          ? Math.round(
              glucose * 10
            ) / 10
          : null,

      bun_mg_dl:
        hasBun
          ? Math.round(
              bun * 10
            ) / 10
          : null,

      paco2_mm_hg:
        hasPaco2
          ? Math.round(
              paco2 * 10
            ) / 10
          : null,

      anion_gap_meq_l:
        anionGap === null
          ? null
          : Math.round(
              anionGap * 10
            ) / 10,

      albumin_corrected_anion_gap_meq_l:
        correctedAg === null
          ? null
          : Math.round(
              correctedAg * 10
            ) / 10,

      anion_gap_formula:
        'Na - (Cl + HCO3), potassium excluded',

      albumin_correction_formula:
        'AG + 2.5 * (4 - albumin[g/dL])',

      albumin_correction_applied:
        correctedAg !== null,

      calculated_osmolality_mosm_kg:
        osmolality === null
          ? null
          : Math.round(
              osmolality * 10
            ) / 10,

      osmolality_formula:
        '2*Na + glucose/18 + BUN/2.8',

      corrected_sodium_meq_l:
        correctedSodium === null
          ? null
          : Math.round(
              correctedSodium * 10
            ) / 10,

      corrected_sodium_delta_meq_l:
        sodiumDelta === null
          ? null
          : Math.round(
              sodiumDelta * 10
            ) / 10,

      corrected_sodium_method:
        hasGlucose
          ? 'Na + 1.6*((glucose-100)/100), for glucose above 100 mg/dL'
          : null,

      metabolic_acidosis_confirmed:
        confirmed,

      winter_analysis_applied:
        metabolicAcidosisGate,

      winter_expected_paco2_mm_hg:
        winterExpected === null
          ? null
          : Math.round(
              winterExpected * 10
            ) / 10,

      winter_lower_mm_hg:
        winterLower === null
          ? null
          : Math.round(
              winterLower * 10
            ) / 10,

      winter_upper_mm_hg:
        winterUpper === null
          ? null
          : Math.round(
              winterUpper * 10
            ) / 10,

      winter_compensation_status:
        winterStatus,

      winter_interpretation_pt:
        winterPt,

      winter_interpretation_en:
        winterEn,

      delta_analysis_applied:
        deltaApplied,

      delta_ag_basis:
        deltaBasis,

      delta_ratio:
        deltaRatio === null
          ? null
          : Math.round(
              deltaRatio * 100
            ) / 100,

      delta_interpretation_code:
        deltaCode,

      delta_interpretation_pt:
        deltaPt,

      delta_interpretation_en:
        deltaEn,

      validity_notes_pt:
        validityPt,

      validity_notes_en:
        validityEn,

      interpretation_pt:
        'Resultados matemáticos de apoio à avaliação metabólica/ácido-base. Devem ser integrados ao pH, gasometria, contexto clínico, método laboratorial e tendências seriadas.',

      interpretation_en:
        'Mathematical results supporting metabolic/acid-base assessment. They must be integrated with pH, blood gas data, clinical context, laboratory methodology and serial trends.'
    };
  }


  globalThis.ClinicalTools =
    Object.freeze({
      calculateNews2,
      calculateEgfrCkdEpi2021,
      classifyBrazilPcdtCkdContext,
      classifyCkd,
      calculateKdigoAki,
      calculateHemodynamics,
      calculateOxygenation,
      calculateMetabolicToolkit
    });
})();
