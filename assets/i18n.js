(() => {
  'use strict';

  const SUPPORTED = new Set([
    'pt-BR',
    'en-GB'
  ]);

  const DEFAULT_LANGUAGE = 'pt-BR';
  const STORAGE_KEY = 'clinical-hub-language';

  const messages = {
    'pt-BR': {
      'nav.subtitle':
        'SAE / NNN & Políticas Nacionais do SUS',

      'nav.sae':
        'Diagnósticos SAE',

      'nav.policy':
        'Políticas (SUS)',

      'nav.calc':
        'Calculadoras',

      'nav.scales':
        'Escalas Clínicas',

      'status.checking':
        'Verificando API...',

      'news2.title':
        'NEWS2 · Deterioração Clínica',

      'news2.description':
        'National Early Warning Score 2 para avaliação de deterioração clínica aguda.',

      'news2.rr':
        'Frequência respiratória (irpm)',

      'news2.spo2':
        'SpO₂ (%)',

      'news2.scale':
        'Escala de SpO₂',

      'news2.scale1':
        'Escala 1',

      'news2.scale2':
        'Escala 2 · alvo 88–92%',

      'news2.scale2confirm':
        'Confirmo que o alvo 88–92% foi definido sob direção clínica qualificada.',

      'news2.oxygen':
        'Paciente recebendo oxigênio suplementar',

      'news2.sbp':
        'Pressão arterial sistólica (mmHg)',

      'news2.pulse':
        'Pulso (bpm)',

      'news2.consciousness':
        'Consciência / nova confusão',

      'news2.alert':
        'Alerta',

      'news2.confusion':
        'Nova confusão',

      'news2.voice':
        'Responde à voz',

      'news2.pain':
        'Responde à dor',

      'news2.unresponsive':
        'Não responsivo',

      'news2.temperature':
        'Temperatura (°C)',

      'news2.calculate':
        'Calcular NEWS2',

      'news2.result':
        'Pontuação NEWS2',

      'news2.monitoring':
        'Monitorização',

      'news2.response':
        'Resposta clínica',

      'news2.source':
        'Fonte',

      'news2.translation':
        'PT-BR é tradução local informativa; consulte o material original do RCP antes do uso clínico.',

      'news2.offline':
        'Resultado calculado localmente em modo offline.',

      'news2.scale2Required':
        'A Escala 2 exige confirmação explícita de alvo 88–92% definido sob direção clínica qualificada.',

      'news2.invalid':
        'Preencha todos os parâmetros NEWS2 com valores válidos.',

      'renal.title':
        'Suite Renal · KDIGO / CKD-EPI',

      'renal.description':
        'TFGe CKD-EPI 2021, classificação KDIGO 2024 de DRC e estadiamento KDIGO 2012 de LRA.',

      'renal.egfrTitle':
        'TFGe · CKD-EPI 2021',

      'renal.age':
        'Idade (anos)',

      'renal.sex':
        'Sexo usado pela equação',

      'renal.female':
        'Feminino',

      'renal.male':
        'Masculino',

      'renal.creatinine':
        'Creatinina sérica',

      'renal.unit':
        'Unidade',

      'renal.calculateEgfr':
        'Calcular TFGe',

      'renal.ckdTitle':
        'DRC · KDIGO 2024',

      'renal.egfrValue':
        'TFGe (mL/min/1,73 m²)',

      'renal.acr':
        'Relação albumina/creatinina urinária',

      'renal.acrOptional':
        'RAC urinária · opcional',

      'renal.chronicity':
        'Anormalidade renal presente por pelo menos 3 meses',

      'renal.otherMarker':
        'Há outro marcador de dano renal',

      'renal.classifyCkd':
        'Classificar G/A e avaliar critérios de DRC',

      'renal.akiTitle':
        'LRA · KDIGO 2012',

      'renal.currentCr':
        'Creatinina atual · opcional',

      'renal.baselineCr':
        'Creatinina basal · opcional',

      'renal.intervalHours':
        'Intervalo basal→atual (horas)',

      'renal.weight':
        'Peso (kg) para diurese',

      'renal.urine':
        'Diurese total (mL)',

      'renal.urineHours':
        'Período da diurese (horas)',

      'renal.anuriaHours':
        'Duração da anúria (horas)',

      'renal.krt':
        'Terapia renal substitutiva iniciada',

      'renal.stageAki':
        'Avaliar / estadiar LRA',

      'renal.result':
        'Resultado',

      'renal.offline':
        'Resultado calculado localmente em modo offline.',

      'renal.invalidEgfr':
        'Informe idade adulta, sexo e creatinina sérica válidos.',

      'renal.invalidCkd':
        'Informe uma TFGe válida e, se utilizada, uma RAC não negativa.',

      'renal.akiBaselineNeedsCurrent':
        'Creatinina basal só pode ser avaliada quando a creatinina atual também é informada.',

      'renal.akiUrineGroup':
        'Para avaliar diurese, informe conjuntamente peso, volume urinário e duração.',

      'renal.source':
        'Fontes: CKD-EPI 2021 / National Kidney Foundation; KDIGO CKD 2024; KDIGO AKI 2012.'
    },

    'en-GB': {
      'nav.subtitle':
        'SAE / NNN & Brazilian National Health Policies',

      'nav.sae':
        'SAE Diagnoses',

      'nav.policy':
        'Policies (SUS)',

      'nav.calc':
        'Calculators',

      'nav.scales':
        'Clinical Scales',

      'status.checking':
        'Checking API...',

      'news2.title':
        'NEWS2 · Clinical Deterioration',

      'news2.description':
        'National Early Warning Score 2 for assessment of acute clinical deterioration.',

      'news2.rr':
        'Respiration rate (breaths/min)',

      'news2.spo2':
        'SpO₂ (%)',

      'news2.scale':
        'SpO₂ scale',

      'news2.scale1':
        'Scale 1',

      'news2.scale2':
        'Scale 2 · target 88–92%',

      'news2.scale2confirm':
        'I confirm that the 88–92% target was set under qualified clinical direction.',

      'news2.oxygen':
        'Patient receiving supplemental oxygen',

      'news2.sbp':
        'Systolic blood pressure (mmHg)',

      'news2.pulse':
        'Pulse (beats/min)',

      'news2.consciousness':
        'Consciousness / new confusion',

      'news2.alert':
        'Alert',

      'news2.confusion':
        'New confusion',

      'news2.voice':
        'Responds to voice',

      'news2.pain':
        'Responds to pain',

      'news2.unresponsive':
        'Unresponsive',

      'news2.temperature':
        'Temperature (°C)',

      'news2.calculate':
        'Calculate NEWS2',

      'news2.result':
        'NEWS2 score',

      'news2.monitoring':
        'Monitoring',

      'news2.response':
        'Clinical response',

      'news2.source':
        'Source',

      'news2.translation':
        'The PT-BR presentation is a local informational translation; consult the original RCP material before clinical use.',

      'news2.offline':
        'Result calculated locally while offline.',

      'news2.scale2Required':
        'Scale 2 requires explicit confirmation of an 88–92% target set under qualified clinical direction.',

      'news2.invalid':
        'Complete all NEWS2 parameters with valid values.',

      'renal.title':
        'Renal Suite · KDIGO / CKD-EPI',

      'renal.description':
        'CKD-EPI 2021 eGFR, KDIGO 2024 CKD classification and KDIGO 2012 AKI staging.',

      'renal.egfrTitle':
        'eGFR · CKD-EPI 2021',

      'renal.age':
        'Age (years)',

      'renal.sex':
        'Sex used by the equation',

      'renal.female':
        'Female',

      'renal.male':
        'Male',

      'renal.creatinine':
        'Serum creatinine',

      'renal.unit':
        'Unit',

      'renal.calculateEgfr':
        'Calculate eGFR',

      'renal.ckdTitle':
        'CKD · KDIGO 2024',

      'renal.egfrValue':
        'eGFR (mL/min/1.73 m²)',

      'renal.acr':
        'Urine albumin-to-creatinine ratio',

      'renal.acrOptional':
        'Urine ACR · optional',

      'renal.chronicity':
        'Kidney abnormality present for at least 3 months',

      'renal.otherMarker':
        'Another marker of kidney damage is present',

      'renal.classifyCkd':
        'Classify G/A and assess CKD criteria',

      'renal.akiTitle':
        'AKI · KDIGO 2012',

      'renal.currentCr':
        'Current creatinine · optional',

      'renal.baselineCr':
        'Baseline creatinine · optional',

      'renal.intervalHours':
        'Baseline→current interval (hours)',

      'renal.weight':
        'Weight (kg) for urine output',

      'renal.urine':
        'Total urine output (mL)',

      'renal.urineHours':
        'Urine-output period (hours)',

      'renal.anuriaHours':
        'Anuria duration (hours)',

      'renal.krt':
        'Kidney replacement therapy initiated',

      'renal.stageAki':
        'Assess / stage AKI',

      'renal.result':
        'Result',

      'renal.offline':
        'Result calculated locally while offline.',

      'renal.invalidEgfr':
        'Enter a valid adult age, sex and serum creatinine.',

      'renal.invalidCkd':
        'Enter a valid eGFR and, when supplied, a non-negative ACR.',

      'renal.akiBaselineNeedsCurrent':
        'Baseline creatinine can only be assessed when current creatinine is also supplied.',

      'renal.akiUrineGroup':
        'To assess urine output, provide weight, urine volume and duration together.',

      'renal.source':
        'Sources: CKD-EPI 2021 / National Kidney Foundation; KDIGO CKD 2024; KDIGO AKI 2012.'
    }
  };


  function loadLanguage() {
    try {
      const value = localStorage.getItem(
        STORAGE_KEY
      );

      if (SUPPORTED.has(value)) {
        return value;
      }
    } catch (_) {}

    return DEFAULT_LANGUAGE;
  }


  let currentLanguage = loadLanguage();


  function t(
    key,
    language = currentLanguage
  ) {
    return (
      messages[language]?.[key]
      ?? messages[DEFAULT_LANGUAGE]?.[key]
      ?? key
    );
  }


  function applyLanguage(language) {
    if (!SUPPORTED.has(language)) {
      language = DEFAULT_LANGUAGE;
    }

    currentLanguage = language;

    try {
      localStorage.setItem(
        STORAGE_KEY,
        language
      );
    } catch (_) {}

    document.documentElement.lang = language;
    document.documentElement.dataset.uiLanguage =
      language;

    document
      .querySelectorAll('[data-i18n]')
      .forEach((element) => {
        element.textContent = t(
          element.dataset.i18n,
          language
        );
      });

    for (const lang of SUPPORTED) {
      const button = document.querySelector(
        `[data-language="${lang}"]`
      );

      if (!button) continue;

      const selected = lang === language;

      button.setAttribute(
        'aria-pressed',
        selected ? 'true' : 'false'
      );

      button.className = selected
        ? 'px-2 py-1 rounded-md bg-teal-600 text-white font-bold'
        : 'px-2 py-1 rounded-md text-slate-400 hover:text-white';
    }

    if (
      typeof globalThis.dispatchEvent === 'function'
      && typeof CustomEvent === 'function'
    ) {
      globalThis.dispatchEvent(
        new CustomEvent(
          'clinical-language-change',
          {
            detail: {
              language
            }
          }
        )
      );
    }
  }


  document.addEventListener(
    'DOMContentLoaded',
    () => {
      document
        .querySelectorAll('[data-language]')
        .forEach((button) => {
          button.addEventListener(
            'click',
            () => {
              applyLanguage(
                button.dataset.language
              );
            }
          );
        });

      applyLanguage(
        currentLanguage
      );
    }
  );


  globalThis.ClinicalI18n = Object.freeze({
    t,

    setLanguage:
      applyLanguage,

    getLanguage:
      () => currentLanguage,

    supportedLanguages:
      Object.freeze([
        'pt-BR',
        'en-GB'
      ])
  });
})();
