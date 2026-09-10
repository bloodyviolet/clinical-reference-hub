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


  globalThis.ClinicalTools =
    Object.freeze({
      calculateNews2
    });
})();
