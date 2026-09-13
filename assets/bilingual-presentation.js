(() => {
  'use strict';

  const TEXT = Object.freeze({
    'pt-BR': Object.freeze({
      homeAria:
        'Clinical Reference Hub · Início',

      languageAria:
        'Idioma',

      dashboardAria:
        'Seções do painel',

      calculatorGroupsAria:
        'Grupos de calculadoras',

      scaleGroupsAria:
        'Grupos de escalas clínicas',

      saeTitle:
        'Buscar Diagnóstico NANDA',

      saeInstruction:
        'Digite o código (ex: 00355) ou palavra-chave (ex: ansiedade) para links NIC/NOC.',

      saeMapping:
        'Mapeamentos primários curados para NANDA-I 2024–2026 (13ª ed.), NIC 8ª ed. e NOC 7ª ed., com nível de confiança e referência por diagnóstico. Não constituem crosswalk oficial e exigem julgamento clínico.',

      saeSearchAria:
        'Buscar diagnóstico por código ou palavra-chave',

      saePlaceholder:
        'Ex: 00355, ansiedade, pain...',

      saeSubmit:
        'Consultar',

      policyTitle:
        'Diretrizes e Políticas de Saúde Pública',

      policyInstruction:
        'Selecione uma política do Ministério da Saúde para carregar suas diretrizes operacionais.',

      policyPdf:
        'Documento Oficial (PDF)',

      policyLoading:
        'Carregando diretrizes...',

      dripTitle:
        'Cálculo de Gotejamento',

      dripVolume:
        'Volume Total (mL)',

      dripTime:
        'Tempo',

      dripUnit:
        'Unidade',

      dripHours:
        'Horas',

      dripMinutes:
        'Minutos',

      dripCalculate:
        'Calcular Fluxo',

      dripFactors:
        'Fatores padrão exibidos: macrogotas 20 gotas/mL · microgotas 60 microgotas/mL. Confirme o fator nominal do equipo utilizado.',

      medsTitle:
        'Dosagem (Regra de Três)',

      medsPrescribed:
        'Dose Prescrita',

      medsAvailable:
        'Dose Disponível',

      medsVolume:
        'Vol. Disponível (mL)',

      medsPrescribedAria:
        'Unidade da dose prescrita',

      medsAvailableAria:
        'Unidade da dose disponível',

      medsCalculate:
        'Calcular Volume a Aspirar',

      example1:
        'Ex: 1',

      example500:
        'Ex: 500',

      example5:
        'Ex: 5',

      bmiTitle:
        'IMC (OMS/OPAS)',

      weight:
        'Peso (kg)',

      height:
        'Altura (m)',

      patientAge:
        'Idade do Paciente',

      bmiCalculate:
        'Calcular IMC',

      example175:
        'Ex: 1.75',

      pedTitle:
        'Regra de Holliday-Segar',

      childWeight:
        'Peso da Criança (kg)',

      pedCalculate:
        'Calcular Hidratação',

      crclTitle:
        'Cockcroft-Gault (CrCl)',

      age:
        'Idade',

      creatinine:
        'Cr (mg/dL)',

      sex:
        'Sexo',

      crclCalculate:
        'Calcular Clearance',

      obstetricsTitle:
        'Obstetrícia',

      lmp:
        'Data da Última Menstruação (DUM)',

      eddButton:
        'DPP',

      fundalHeight:
        'Altura Uterina em cm (Regra de McDonald)',

      gaButton:
        'IG',

      example24:
        'Ex: 24',

      apgarTitle:
        'Índice de Apgar',

      apgarTime:
        'Momento da avaliação',

      select:
        'Selecione...',

      minute1:
        '1 minuto',

      minute5:
        '5 minutos',

      minute10:
        '10 minutos / reavaliação',

      apgarAppearance:
        'Aparência (Cor)',

      apgarPink:
        '2 - Rosado',

      apgarAcrocyanosis:
        '1 - Acrocianose',

      apgarCentralCyanosis:
        '0 - Cianose central',

      apgarPulse:
        'Pulso (FC)',

      apgarAbsent:
        '0 - Ausente',

      apgarGrimace:
        'Gesticulação',

      apgarCryCough:
        '2 - Choro/Tosse',

      apgarFacialGrimace:
        '1 - Careta',

      apgarNoResponse:
        '0 - Sem resposta',

      apgarActivity:
        'Atividade (Tônus)',

      apgarActive:
        '2 - Movimento Ativo',

      apgarSomeFlexion:
        '1 - Flexão leve',

      apgarFlaccid:
        '0 - Flácido',

      apgarRespiration:
        'Respiração',

      apgarStrongCry:
        '2 - Choro forte / Regular',

      apgarWeak:
        '1 - Fraco / Irregular',

      apgarScore:
        'Pontuação Apgar'
    }),

    'en-GB': Object.freeze({
      homeAria:
        'Clinical Reference Hub · Home',

      languageAria:
        'Language',

      dashboardAria:
        'Dashboard sections',

      calculatorGroupsAria:
        'Calculator groups',

      scaleGroupsAria:
        'Clinical scale groups',

      saeTitle:
        'Search NANDA Diagnosis',

      saeInstruction:
        'Enter a code (e.g. 00355) or keyword (e.g. anxiety) to retrieve NIC/NOC links.',

      saeMapping:
        'Curated primary mappings for NANDA-I 2024–2026 (13th ed.), NIC 8th ed. and NOC 7th ed., with confidence level and diagnosis-level references. They are not an official crosswalk and require clinical judgement.',

      saeSearchAria:
        'Search diagnosis by code or keyword',

      saePlaceholder:
        'e.g. 00355, anxiety, pain...',

      saeSubmit:
        'Search',

      policyTitle:
        'Public Health Policies and Guidance',

      policyInstruction:
        'Select a Brazilian Ministry of Health policy to load its operational guidance.',

      policyPdf:
        'Official Document (PDF)',

      policyLoading:
        'Loading guidance...',

      dripTitle:
        'IV Drip Calculation',

      dripVolume:
        'Total Volume (mL)',

      dripTime:
        'Time',

      dripUnit:
        'Unit',

      dripHours:
        'Hours',

      dripMinutes:
        'Minutes',

      dripCalculate:
        'Calculate Flow',

      dripFactors:
        'Displayed standard factors: macrodrip 20 drops/mL · microdrip 60 microdrops/mL. Confirm the nominal factor of the giving set in use.',

      medsTitle:
        'Medication Dose (Ratio and Proportion)',

      medsPrescribed:
        'Prescribed Dose',

      medsAvailable:
        'Available Dose',

      medsVolume:
        'Available Volume (mL)',

      medsPrescribedAria:
        'Prescribed dose unit',

      medsAvailableAria:
        'Available dose unit',

      medsCalculate:
        'Calculate Volume to Draw Up',

      example1:
        'e.g. 1',

      example500:
        'e.g. 500',

      example5:
        'e.g. 5',

      bmiTitle:
        'BMI (WHO/PAHO)',

      weight:
        'Weight (kg)',

      height:
        'Height (m)',

      patientAge:
        'Patient Age',

      bmiCalculate:
        'Calculate BMI',

      example175:
        'e.g. 1.75',

      pedTitle:
        'Holliday–Segar Rule',

      childWeight:
        'Child Weight (kg)',

      pedCalculate:
        'Calculate Maintenance Fluids',

      crclTitle:
        'Cockcroft–Gault (CrCl)',

      age:
        'Age',

      creatinine:
        'Cr (mg/dL)',

      sex:
        'Sex',

      crclCalculate:
        'Calculate Clearance',

      obstetricsTitle:
        'Obstetrics',

      lmp:
        'Last Menstrual Period (LMP)',

      eddButton:
        'EDD',

      fundalHeight:
        'Fundal Height in cm (McDonald Rule)',

      gaButton:
        'GA',

      example24:
        'e.g. 24',

      apgarTitle:
        'Apgar Score',

      apgarTime:
        'Assessment Time',

      select:
        'Select...',

      minute1:
        '1 minute',

      minute5:
        '5 minutes',

      minute10:
        '10 minutes / reassessment',

      apgarAppearance:
        'Appearance (Colour)',

      apgarPink:
        '2 - Pink',

      apgarAcrocyanosis:
        '1 - Acrocyanosis',

      apgarCentralCyanosis:
        '0 - Central cyanosis',

      apgarPulse:
        'Pulse (HR)',

      apgarAbsent:
        '0 - Absent',

      apgarGrimace:
        'Grimace',

      apgarCryCough:
        '2 - Cry/Cough',

      apgarFacialGrimace:
        '1 - Facial grimace',

      apgarNoResponse:
        '0 - No response',

      apgarActivity:
        'Activity (Tone)',

      apgarActive:
        '2 - Active movement',

      apgarSomeFlexion:
        '1 - Some flexion',

      apgarFlaccid:
        '0 - Flaccid',

      apgarRespiration:
        'Respiration',

      apgarStrongCry:
        '2 - Strong cry / Regular',

      apgarWeak:
        '1 - Weak / Irregular',

      apgarScore:
        'Apgar Score'
    })
  });


  function language() {
    return (
      globalThis
        .ClinicalI18n
        ?.getLanguage?.()
      || 'pt-BR'
    );
  }


  function value(
    key,
    selectedLanguage = language()
  ) {
    return (
      TEXT[
        selectedLanguage
      ]?.[
        key
      ]
      ?? TEXT[
        'pt-BR'
      ][
        key
      ]
      ?? key
    );
  }


  function setText(
    selector,
    key,
    selectedLanguage
  ) {
    const element =
      document.querySelector(
        selector
      );

    if (element) {
      element.textContent =
        value(
          key,
          selectedLanguage
        );
    }
  }


  function setAttribute(
    selector,
    attribute,
    key,
    selectedLanguage
  ) {
    const element =
      document.querySelector(
        selector
      );

    if (element) {
      element.setAttribute(
        attribute,
        value(
          key,
          selectedLanguage
        )
      );
    }
  }


  function setTrailingText(
    element,
    key,
    selectedLanguage
  ) {
    if (!element) {
      return;
    }

    const textNode =
      Array.from(
        element.childNodes
      ).find(
        (node) =>
          node.nodeType === 3
          && node.textContent
            .trim()
            .length > 0
      );

    if (textNode) {
      textNode.textContent =
        value(
          key,
          selectedLanguage
        );

      return;
    }

    element.appendChild(
      document.createTextNode(
        value(
          key,
          selectedLanguage
        )
      )
    );
  }


  function cardHeading(
    formId
  ) {
    return (
      document
        .getElementById(
          formId
        )
        ?.closest(
          '.bg-slate-900'
        )
        ?.querySelector(
          'h2'
        )
      || null
    );
  }


  function setCardHeading(
    formId,
    key,
    selectedLanguage
  ) {
    setTrailingText(
      cardHeading(
        formId
      ),
      key,
      selectedLanguage
    );
  }


  function apply(
    selectedLanguage = language()
  ) {
    if (
      ![
        'pt-BR',
        'en-GB'
      ].includes(
        selectedLanguage
      )
    ) {
      selectedLanguage =
        'pt-BR';
    }


    setAttribute(
      '#brand-home',
      'aria-label',
      'homeAria',
      selectedLanguage
    );


    const languageButton =
      document.querySelector(
        '[data-language="pt-BR"]'
      );

    languageButton
      ?.parentElement
      ?.setAttribute(
        'aria-label',
        value(
          'languageAria',
          selectedLanguage
        )
      );


    setAttribute(
      '[role="tablist"]',
      'aria-label',
      'dashboardAria',
      selectedLanguage
    );

    setAttribute(
      '#calc-subnav',
      'aria-label',
      'calculatorGroupsAria',
      selectedLanguage
    );

    setAttribute(
      '#scale-subnav',
      'aria-label',
      'scaleGroupsAria',
      selectedLanguage
    );


    setText(
      '#view-sae h2',
      'saeTitle',
      selectedLanguage
    );

    setText(
      '#view-sae h2 + p',
      'saeInstruction',
      selectedLanguage
    );

    setText(
      '#view-sae h2 + p + p',
      'saeMapping',
      selectedLanguage
    );

    setAttribute(
      '#sae-input',
      'aria-label',
      'saeSearchAria',
      selectedLanguage
    );

    setAttribute(
      '#sae-input',
      'placeholder',
      'saePlaceholder',
      selectedLanguage
    );

    setText(
      '#sae-search-form button[type="submit"]',
      'saeSubmit',
      selectedLanguage
    );


    setText(
      '#view-policy h2',
      'policyTitle',
      selectedLanguage
    );

    setText(
      '#view-policy h2 + p',
      'policyInstruction',
      selectedLanguage
    );

    setTrailingText(
      document.getElementById(
        'pdf-link'
      ),
      'policyPdf',
      selectedLanguage
    );

    setText(
      '#policy-loading',
      'policyLoading',
      selectedLanguage
    );


    setCardHeading(
      'drip-form',
      'dripTitle',
      selectedLanguage
    );

    setText(
      'label[for="drip-v"]',
      'dripVolume',
      selectedLanguage
    );

    setText(
      'label[for="drip-t"]',
      'dripTime',
      selectedLanguage
    );

    setText(
      'label[for="drip-u"]',
      'dripUnit',
      selectedLanguage
    );

    setText(
      '#drip-u option[value="h"]',
      'dripHours',
      selectedLanguage
    );

    setText(
      '#drip-u option[value="m"]',
      'dripMinutes',
      selectedLanguage
    );

    setText(
      '#drip-form button[type="submit"]',
      'dripCalculate',
      selectedLanguage
    );

    setText(
      '#drip-form + p',
      'dripFactors',
      selectedLanguage
    );


    setCardHeading(
      'meds-form',
      'medsTitle',
      selectedLanguage
    );

    setText(
      'label[for="med-presc"]',
      'medsPrescribed',
      selectedLanguage
    );

    setText(
      'label[for="med-disp"]',
      'medsAvailable',
      selectedLanguage
    );

    setText(
      'label[for="med-vol"]',
      'medsVolume',
      selectedLanguage
    );

    setAttribute(
      '#med-presc',
      'placeholder',
      'example1',
      selectedLanguage
    );

    setAttribute(
      '#med-disp',
      'placeholder',
      'example500',
      selectedLanguage
    );

    setAttribute(
      '#med-vol',
      'placeholder',
      'example5',
      selectedLanguage
    );

    setAttribute(
      '#med-presc-unit',
      'aria-label',
      'medsPrescribedAria',
      selectedLanguage
    );

    setAttribute(
      '#med-disp-unit',
      'aria-label',
      'medsAvailableAria',
      selectedLanguage
    );

    document
      .querySelectorAll(
        '#med-presc-unit option[value="UI"], #med-disp-unit option[value="UI"]'
      )
      .forEach(
        (option) => {
          option.textContent =
            selectedLanguage === 'en-GB'
              ? 'IU'
              : 'UI';
        }
      );

    setText(
      '#meds-form button[type="submit"]',
      'medsCalculate',
      selectedLanguage
    );


    setCardHeading(
      'bmi-form',
      'bmiTitle',
      selectedLanguage
    );

    setText(
      'label[for="bmi-w"]',
      'weight',
      selectedLanguage
    );

    setText(
      'label[for="bmi-h"]',
      'height',
      selectedLanguage
    );

    setText(
      'label[for="bmi-age"]',
      'patientAge',
      selectedLanguage
    );

    setAttribute(
      '#bmi-h',
      'placeholder',
      'example175',
      selectedLanguage
    );

    setText(
      '#bmi-form button[type="submit"]',
      'bmiCalculate',
      selectedLanguage
    );


    setCardHeading(
      'ped-form',
      'pedTitle',
      selectedLanguage
    );

    setText(
      'label[for="ped-w"]',
      'childWeight',
      selectedLanguage
    );

    setText(
      '#ped-form button[type="submit"]',
      'pedCalculate',
      selectedLanguage
    );


    setCardHeading(
      'crcl-form',
      'crclTitle',
      selectedLanguage
    );

    setText(
      'label[for="crcl-age"]',
      'age',
      selectedLanguage
    );

    setText(
      'label[for="crcl-w"]',
      'weight',
      selectedLanguage
    );

    setText(
      'label[for="crcl-cr"]',
      'creatinine',
      selectedLanguage
    );

    setText(
      'label[for="crcl-sex"]',
      'sex',
      selectedLanguage
    );

    setText(
      '#crcl-form button[type="submit"]',
      'crclCalculate',
      selectedLanguage
    );


    setCardHeading(
      'naegele-form',
      'obstetricsTitle',
      selectedLanguage
    );

    setText(
      'label[for="dum-input"]',
      'lmp',
      selectedLanguage
    );

    setText(
      '#naegele-form button[type="submit"]',
      'eddButton',
      selectedLanguage
    );

    setText(
      'label[for="au-input"]',
      'fundalHeight',
      selectedLanguage
    );

    setAttribute(
      '#au-input',
      'placeholder',
      'example24',
      selectedLanguage
    );

    setText(
      '#mcdonald-form button[type="submit"]',
      'gaButton',
      selectedLanguage
    );


    setCardHeading(
      'apgar-form',
      'apgarTitle',
      selectedLanguage
    );

    setText(
      'label[for="apgar-time"]',
      'apgarTime',
      selectedLanguage
    );

    setText(
      '#apgar-time option[value=""]',
      'select',
      selectedLanguage
    );

    setText(
      '#apgar-time option[value="1"]',
      'minute1',
      selectedLanguage
    );

    setText(
      '#apgar-time option[value="5"]',
      'minute5',
      selectedLanguage
    );

    setText(
      '#apgar-time option[value="10"]',
      'minute10',
      selectedLanguage
    );


    setText(
      'label[for="apgar-a"]',
      'apgarAppearance',
      selectedLanguage
    );

    setText(
      '#apgar-a option[value=""]',
      'select',
      selectedLanguage
    );

    setText(
      '#apgar-a option[value="2"]',
      'apgarPink',
      selectedLanguage
    );

    setText(
      '#apgar-a option[value="1"]',
      'apgarAcrocyanosis',
      selectedLanguage
    );

    setText(
      '#apgar-a option[value="0"]',
      'apgarCentralCyanosis',
      selectedLanguage
    );


    setText(
      'label[for="apgar-p"]',
      'apgarPulse',
      selectedLanguage
    );

    setText(
      '#apgar-p option[value=""]',
      'select',
      selectedLanguage
    );

    setText(
      '#apgar-p option[value="0"]',
      'apgarAbsent',
      selectedLanguage
    );


    setText(
      'label[for="apgar-g"]',
      'apgarGrimace',
      selectedLanguage
    );

    setText(
      '#apgar-g option[value=""]',
      'select',
      selectedLanguage
    );

    setText(
      '#apgar-g option[value="2"]',
      'apgarCryCough',
      selectedLanguage
    );

    setText(
      '#apgar-g option[value="1"]',
      'apgarFacialGrimace',
      selectedLanguage
    );

    setText(
      '#apgar-g option[value="0"]',
      'apgarNoResponse',
      selectedLanguage
    );


    setText(
      'label[for="apgar-t"]',
      'apgarActivity',
      selectedLanguage
    );

    setText(
      '#apgar-t option[value=""]',
      'select',
      selectedLanguage
    );

    setText(
      '#apgar-t option[value="2"]',
      'apgarActive',
      selectedLanguage
    );

    setText(
      '#apgar-t option[value="1"]',
      'apgarSomeFlexion',
      selectedLanguage
    );

    setText(
      '#apgar-t option[value="0"]',
      'apgarFlaccid',
      selectedLanguage
    );


    setText(
      'label[for="apgar-r"]',
      'apgarRespiration',
      selectedLanguage
    );

    setText(
      '#apgar-r option[value=""]',
      'select',
      selectedLanguage
    );

    setText(
      '#apgar-r option[value="2"]',
      'apgarStrongCry',
      selectedLanguage
    );

    setText(
      '#apgar-r option[value="1"]',
      'apgarWeak',
      selectedLanguage
    );

    setText(
      '#apgar-r option[value="0"]',
      'apgarAbsent',
      selectedLanguage
    );


    const apgarTotal =
      document.getElementById(
        'apgar-total'
      );

    if (
      apgarTotal
      ?.previousElementSibling
    ) {
      apgarTotal
        .previousElementSibling
        .textContent =
          value(
            'apgarScore',
            selectedLanguage
          );
    }
  }


  globalThis.addEventListener?.(
    'clinical-language-change',
    (event) => {
      apply(
        event?.detail?.language
        || language()
      );
    }
  );


  document.addEventListener(
    'DOMContentLoaded',
    () => {
      apply(
        language()
      );
    }
  );


  globalThis
    .ClinicalBilingualPresentation =
      Object.freeze({
        apply,

        value,

        supportedLanguages:
          Object.freeze([
            'pt-BR',
            'en-GB'
          ])
      });
})();
