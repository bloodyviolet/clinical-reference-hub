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
        'Confusão aguda',

      'news2.voice':
        'Resposta a voz',

      'news2.pain':
        'Resposta a dor',

      'news2.unresponsive':
        'Irresponsivo',

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
        'Terminologia PT-BR harmonizada com a adaptação transcultural brasileira validada. Textos explicativos adicionais são locais; as condições atuais do RCP para material traduzido permanecem aplicáveis.',

      'news2.offline':
        'Resultado calculado localmente em modo offline.',

      'news2.scale2Required':
        'A Escala 2 exige confirmação explícita de alvo 88–92% definido sob direção clínica qualificada.',

      'news2.invalid':
        'Preencha todos os parâmetros NEWS2 com valores válidos.',

      'renal.title':
        'Suite Renal · KDIGO / CKD-EPI / SUS',

      'renal.description':
        'TFGe CKD-EPI 2021, classificação internacional KDIGO, contexto nacional SUS/PCDT e estadiamento KDIGO 2012 de LRA.',

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
        'DRC · KDIGO 2024 + SUS PCDT',

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
        'Fontes: CKD-EPI 2021 / NKF; SBN/SBPC-ML 2024 + errata 2025; KDIGO CKD 2024; PCDT DRC MS 2024/2025; KDIGO AKI 2012 + Ministério da Saúde.',

      'renal.egfrBrazilAlignment':
        'Brasil: CKD-EPI 2021 sem coeficiente de raça está alinhada ao consenso SBN/SBPC-ML 2024; a errata brasileira de 2025 confirma o expoente -1,200 já implementado.',

      'renal.internationalTitle':
        'Internacional · KDIGO 2024',

      'renal.brazilTitle':
        'Brasil · SUS PCDT DRC 2024/2025',

      'renal.onDialysis':
        'Paciente em diálise para contexto de estágio 5D do PCDT',

      'renal.pcdtStage':
        'Estágio SUS PCDT',

      'renal.pcdtAcr':
        'RAC SUS PCDT',

      'renal.pcdtEquationBlocked':
        'A equação impressa no PCDT não é executada por conflitos de fonte verificados; nenhum dado de raça ou ancestralidade é usado.',

      'renal.pcdtNotice':
        'Brasil/SUS: o PCDT nacional é exibido como contexto de política e estadiamento. Sua equação impressa não é usada para recalcular a TFGe.',

      'renal.akiBrazilAlignment':
        'Brasil: a Linha de Cuidado do Ministério da Saúde utiliza a classificação KDIGO 2012; não há segundo algoritmo numérico brasileiro.',

      'hemo.title':
        'Hemodinâmica · PAM / Pressão de Pulso / SI / MSI',

      'hemo.description':
        'Cálculos hemodinâmicos neutros a partir de PAS, PAD e frequência cardíaca, com orientação brasileira opcional dependente do contexto clínico.',

      'hemo.sbp':
        'Pressão arterial sistólica (mmHg)',

      'hemo.dbp':
        'Pressão arterial diastólica (mmHg)',

      'hemo.hr':
        'Frequência cardíaca (bpm)',

      'hemo.context':
        'Contexto clínico opcional · Brasil',

      'hemo.contextNone':
        'Nenhum · cálculo hemodinâmico genérico',

      'hemo.contextSeptic':
        'Choque séptico · orientação contextual de PAM',

      'hemo.contextObstetric':
        'Hemorragia obstétrica · orientação contextual de Shock Index',

      'hemo.contextHelp':
        'A seleção apenas adiciona orientação brasileira dependente do contexto. Ela não altera as fórmulas nem cria um ponto de corte universal.',

      'hemo.contextResult':
        'Orientação brasileira contextual',

      'hemo.calculate':
        'Calcular índices hemodinâmicos',

      'hemo.result':
        'Índices calculados',

      'hemo.pp':
        'Pressão de pulso',

      'hemo.map':
        'Pressão arterial média',

      'hemo.si':
        'Shock Index',

      'hemo.msi':
        'Modified Shock Index',

      'hemo.offline':
        'Resultado calculado localmente em modo offline.',

      'hemo.invalid':
        'Informe PAS, PAD e frequência cardíaca válidas. A PAS não pode ser menor que a PAD.',

      'hemo.noThreshold':
        'Nenhum ponto de corte universal de PAM, pressão de pulso, SI ou MSI foi aplicado.',

      'hemo.source':
        'Fórmulas: PAM ≈ PAD + ⅓(PAS−PAD); PP = PAS−PAD; SI = FC/PAS; MSI = FC/PAM.',

      'hemo.brazilSource':
        'Brasil: PAM 65 mmHg é apresentada somente no contexto selecionado de choque séptico; Shock Index >0,9 somente no contexto selecionado de hemorragia obstétrica.',

      'oxygen.title':
        'Oxigenação · Relações P/F e S/F',

      'oxygen.description':
        'Cálculo das relações PaO₂/FiO₂ e SpO₂/FiO₂ com FiO₂ explicitamente informada.',

      'oxygen.fio2':
        'FiO₂ (%)',

      'oxygen.pao2':
        'PaO₂ (mmHg) · opcional',

      'oxygen.spo2':
        'SpO₂ (%) · opcional',

      'oxygen.calculate':
        'Calcular relações de oxigenação',

      'oxygen.result':
        'Relações calculadas',

      'oxygen.pf':
        'Relação P/F',

      'oxygen.sf':
        'Relação S/F',

      'oxygen.offline':
        'Resultado calculado localmente em modo offline.',

      'oxygen.invalid':
        'Informe FiO₂ entre 21% e 100% e pelo menos PaO₂ ou SpO₂ válida.',

      'oxygen.sfCaution':
        'Atenção à interpretação da relação S/F',

      'oxygen.noArdsDiagnosis':
        'A relação isolada não estabelece diagnóstico nem gravidade de SDRA.',

      'oxygen.fio2Explicit':
        'A FiO₂ deve ser conhecida; o sistema não a estima a partir do fluxo ou do dispositivo.',

      'oxygen.source':
        'P/F = PaO₂ / FiO₂ em fração · S/F = SpO₂ / FiO₂ em fração.',

      'metabolic.title':
        'Ácido-base e metabolismo',

      'metabolic.description':
        'Ânion gap, correção por albumina, osmolalidade calculada, sódio corrigido, Winter e delta ratio com gates explícitos de validade.',

      'metabolic.sodium':
        'Sódio (mEq/L)',

      'metabolic.chloride':
        'Cloreto (mEq/L) · opcional',

      'metabolic.bicarbonate':
        'Bicarbonato / HCO₃⁻ (mEq/L) · opcional',

      'metabolic.albumin':
        'Albumina (g/dL) · opcional',

      'metabolic.glucose':
        'Glicose (mg/dL) · opcional',

      'metabolic.bun':
        'BUN (mg/dL) · opcional',

      'metabolic.paco2':
        'PaCO₂ (mmHg) · opcional',

      'metabolic.confirmed':
        'Acidose metabólica foi confirmada clinicamente/gasometricamente',

      'metabolic.gateWarning':
        'Marque esta opção somente quando acidose metabólica já tiver sido estabelecida. O sistema não infere o distúrbio primário a partir destes valores.',

      'metabolic.calculate':
        'Calcular painel metabólico',

      'metabolic.result':
        'Resultados calculados',

      'metabolic.ag':
        'Ânion gap',

      'metabolic.correctedAg':
        'Ânion gap corrigido por albumina',

      'metabolic.osmolality':
        'Osmolalidade calculada',

      'metabolic.correctedNa':
        'Sódio corrigido',

      'metabolic.winter':
        'Compensação de Winter',

      'metabolic.delta':
        'Delta ratio',

      'metabolic.validity':
        'Validade / limitações',

      'metabolic.offline':
        'Resultado calculado localmente em modo offline.',

      'metabolic.invalid':
        'Informe um sódio válido e dados suficientes para pelo menos um cálculo metabólico.',

      'metabolic.agPair':
        'Cloreto e bicarbonato devem ser informados conjuntamente.',

      'metabolic.albuminNeedsAg':
        'A correção por albumina exige cloreto e bicarbonato.',

      'metabolic.bunNeedsGlucose':
        'O cálculo de osmolalidade exige glicose quando BUN é informado.',

      'metabolic.noPath':
        'Informe cloreto + bicarbonato e/ou glicose para realizar pelo menos um cálculo.',

      'metabolic.source':
        'AG = Na−(Cl+HCO₃) · AG corrigido = AG+2,5×(4−albumina) · Osm = 2Na+glicose/18+BUN/2,8 · Na corrigido: fator 1,6.',

      'growth.title':
        'Crescimento pediátrico · WHO / SISVAN',

      'growth.description':
        'Escores-z e percentis WHO com interpretação brasileira SISVAN separada.',

      'growth.sex':
        'Sexo da referência WHO',

      'growth.male':
        'Masculino',

      'growth.female':
        'Feminino',

      'growth.age':
        'Idade',

      'growth.ageUnit':
        'Unidade da idade',

      'growth.days':
        'Dias',

      'growth.months':
        'Meses',

      'growth.ageBasis':
        'Base da idade',

      'growth.chronological':
        'Idade cronológica',

      'growth.corrected':
        'Idade corrigida',

      'growth.correctedNote':
        'Selecione idade corrigida somente quando ela já tiver sido calculada para uma criança prematura; a idade cronológica deve permanecer registrada separadamente.',

      'growth.weight':
        'Peso (kg) · opcional',

      'growth.lengthHeight':
        'Comprimento / estatura (cm) · opcional',

      'growth.position':
        'Posição da medida',

      'growth.positionSelect':
        'Selecione...',

      'growth.length':
        'Comprimento recumbente',

      'growth.height':
        'Estatura em pé',

      'growth.head':
        'Perímetro cefálico (cm) · opcional',

      'growth.oedema':
        'Edema presente',

      'growth.calculate':
        'Calcular crescimento',

      'growth.results':
        'Resultados de crescimento',

      'growth.wfa':
        'Peso para idade',

      'growth.hfa':
        'Comprimento / estatura para idade',

      'growth.wflh':
        'Peso para comprimento / estatura',

      'growth.bfa':
        'IMC para idade',

      'growth.hcfa':
        'Perímetro cefálico para idade',

      'growth.z':
        'Escore-z',

      'growth.percentile':
        'Percentil',

      'growth.percentileUnavailable':
        'Indisponível fora de ±3 DP',

      'growth.who':
        'WHO',

      'growth.brazil':
        'Brasil · SISVAN',

      'growth.noNamedClass':
        'Sem classificação nominal adicional',

      'growth.warning':
        'Observações / alertas',

      'growth.adjustment':
        'Ajuste de posição aplicado',

      'growth.bmi':
        'IMC calculado',

      'growth.offline':
        'Resultado calculado localmente com as tabelas WHO precacheadas.',

      'growth.invalid':
        'Informe sexo, idade válida e pelo menos uma medida antropométrica.',

      'growth.positionRequired':
        'Informe se a medida foi obtida como comprimento recumbente ou estatura em pé.',

      'growth.source':
        'Referências numéricas: WHO 2006/2007 · interpretação nacional: Ministério da Saúde / SISVAN.',

      'growth.noEndorsement':
        'A WHO não endossa este aplicativo nem seus resultados.',

      'growth.attribution':
        'Tabelas e proveniência: assets/reference/who-growth/NOTICE.txt.'
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
        'Renal Suite · KDIGO / CKD-EPI / SUS',

      'renal.description':
        'CKD-EPI 2021 eGFR, international KDIGO classification, national SUS/PCDT context and KDIGO 2012 AKI staging.',

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
        'CKD · KDIGO 2024 + SUS PCDT',

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
        'Sources: CKD-EPI 2021 / NKF; SBN/SBPC-ML 2024 + 2025 erratum; KDIGO CKD 2024; Brazilian Ministry CKD PCDT 2024/2025; KDIGO AKI 2012 + Ministry of Health.',

      'renal.egfrBrazilAlignment':
        'Brazil: race-free CKD-EPI 2021 aligns with the 2024 SBN/SBPC-ML consensus; the 2025 Brazilian erratum confirms the -1.200 exponent already implemented.',

      'renal.internationalTitle':
        'International · KDIGO 2024',

      'renal.brazilTitle':
        'Brazil · SUS CKD PCDT 2024/2025',

      'renal.onDialysis':
        'Patient is on dialysis for PCDT stage-5D context',

      'renal.pcdtStage':
        'SUS PCDT stage',

      'renal.pcdtAcr':
        'SUS PCDT ACR',

      'renal.pcdtEquationBlocked':
        'The equation printed in the PCDT is not executed because of verified source conflicts; no race or ancestry input is used.',

      'renal.pcdtNotice':
        'Brazil/SUS: the national PCDT is shown as policy and staging context. Its printed equation is not used to recalculate eGFR.',

      'renal.akiBrazilAlignment':
        'Brazil: the Ministry of Health care pathway uses KDIGO 2012 classification; there is no second Brazilian numerical algorithm.',

      'hemo.title':
        'Haemodynamics · MAP / Pulse Pressure / SI / MSI',

      'hemo.description':
        'Threshold-neutral haemodynamic calculations from SBP, DBP and heart rate, with optional context-dependent Brazilian guidance.',

      'hemo.sbp':
        'Systolic blood pressure (mmHg)',

      'hemo.dbp':
        'Diastolic blood pressure (mmHg)',

      'hemo.hr':
        'Heart rate (beats/min)',

      'hemo.context':
        'Optional clinical context · Brazil',

      'hemo.contextNone':
        'None · generic haemodynamic calculation',

      'hemo.contextSeptic':
        'Septic shock · contextual MAP guidance',

      'hemo.contextObstetric':
        'Obstetric haemorrhage · contextual Shock Index guidance',

      'hemo.contextHelp':
        'Selection only adds context-dependent Brazilian guidance. It does not alter the formulae or create a universal cut-off.',

      'hemo.contextResult':
        'Contextual Brazilian guidance',

      'hemo.calculate':
        'Calculate haemodynamic indices',

      'hemo.result':
        'Calculated indices',

      'hemo.pp':
        'Pulse pressure',

      'hemo.map':
        'Mean arterial pressure',

      'hemo.si':
        'Shock Index',

      'hemo.msi':
        'Modified Shock Index',

      'hemo.offline':
        'Result calculated locally while offline.',

      'hemo.invalid':
        'Enter valid SBP, DBP and heart rate values. SBP cannot be lower than DBP.',

      'hemo.noThreshold':
        'No universal MAP, pulse-pressure, SI or MSI cut-off has been applied.',

      'hemo.source':
        'Formulae: MAP ≈ DBP + ⅓(SBP−DBP); PP = SBP−DBP; SI = HR/SBP; MSI = HR/MAP.',

      'hemo.brazilSource':
        'Brazil: MAP 65 mmHg is shown only in the selected septic-shock context; Shock Index >0.9 only in the selected obstetric-haemorrhage context.',

      'oxygen.title':
        'Oxygenation · P/F and S/F Ratios',

      'oxygen.description':
        'Calculation of PaO₂/FiO₂ and SpO₂/FiO₂ ratios using explicitly supplied FiO₂.',

      'oxygen.fio2':
        'FiO₂ (%)',

      'oxygen.pao2':
        'PaO₂ (mmHg) · optional',

      'oxygen.spo2':
        'SpO₂ (%) · optional',

      'oxygen.calculate':
        'Calculate oxygenation ratios',

      'oxygen.result':
        'Calculated ratios',

      'oxygen.pf':
        'P/F ratio',

      'oxygen.sf':
        'S/F ratio',

      'oxygen.offline':
        'Result calculated locally while offline.',

      'oxygen.invalid':
        'Enter FiO₂ between 21% and 100% and at least one valid PaO₂ or SpO₂ value.',

      'oxygen.sfCaution':
        'S/F ratio interpretation caution',

      'oxygen.noArdsDiagnosis':
        'The ratio alone does not establish an ARDS diagnosis or severity.',

      'oxygen.fio2Explicit':
        'FiO₂ must be known; the system does not estimate it from flow rate or delivery-device type.',

      'oxygen.source':
        'P/F = PaO₂ / FiO₂ fraction · S/F = SpO₂ / FiO₂ fraction.',

      'metabolic.title':
        'Acid-base and metabolic toolkit',

      'metabolic.description':
        'Anion gap, albumin correction, calculated osmolality, corrected sodium, Winter compensation and delta ratio with explicit validity gates.',

      'metabolic.sodium':
        'Sodium (mEq/L)',

      'metabolic.chloride':
        'Chloride (mEq/L) · optional',

      'metabolic.bicarbonate':
        'Bicarbonate / HCO₃⁻ (mEq/L) · optional',

      'metabolic.albumin':
        'Albumin (g/dL) · optional',

      'metabolic.glucose':
        'Glucose (mg/dL) · optional',

      'metabolic.bun':
        'BUN (mg/dL) · optional',

      'metabolic.paco2':
        'PaCO₂ (mmHg) · optional',

      'metabolic.confirmed':
        'Metabolic acidosis has been clinically/blood-gas confirmed',

      'metabolic.gateWarning':
        'Select this only when metabolic acidosis has already been established. The system does not infer the primary disorder from these values.',

      'metabolic.calculate':
        'Calculate metabolic panel',

      'metabolic.result':
        'Calculated results',

      'metabolic.ag':
        'Anion gap',

      'metabolic.correctedAg':
        'Albumin-corrected anion gap',

      'metabolic.osmolality':
        'Calculated osmolality',

      'metabolic.correctedNa':
        'Corrected sodium',

      'metabolic.winter':
        'Winter compensation',

      'metabolic.delta':
        'Delta ratio',

      'metabolic.validity':
        'Validity / limitations',

      'metabolic.offline':
        'Result calculated locally while offline.',

      'metabolic.invalid':
        'Enter a valid sodium value and sufficient data for at least one metabolic calculation.',

      'metabolic.agPair':
        'Chloride and bicarbonate must be supplied together.',

      'metabolic.albuminNeedsAg':
        'Albumin correction requires chloride and bicarbonate.',

      'metabolic.bunNeedsGlucose':
        'Calculated osmolality requires glucose when BUN is supplied.',

      'metabolic.noPath':
        'Provide chloride + bicarbonate and/or glucose to perform at least one calculation.',

      'metabolic.source':
        'AG = Na−(Cl+HCO₃) · corrected AG = AG+2.5×(4−albumin) · Osm = 2Na+glucose/18+BUN/2.8 · corrected Na: 1.6 factor.',

      'growth.title':
        'Paediatric growth · WHO / SISVAN',

      'growth.description':
        'WHO z-scores and percentiles with a separate Brazilian SISVAN interpretation layer.',

      'growth.sex':
        'WHO reference sex',

      'growth.male':
        'Male',

      'growth.female':
        'Female',

      'growth.age':
        'Age',

      'growth.ageUnit':
        'Age unit',

      'growth.days':
        'Days',

      'growth.months':
        'Months',

      'growth.ageBasis':
        'Age basis',

      'growth.chronological':
        'Chronological age',

      'growth.corrected':
        'Corrected age',

      'growth.correctedNote':
        'Select corrected age only when it has already been calculated for a preterm child; chronological age should remain recorded separately.',

      'growth.weight':
        'Weight (kg) · optional',

      'growth.lengthHeight':
        'Length / height (cm) · optional',

      'growth.position':
        'Measurement position',

      'growth.positionSelect':
        'Select...',

      'growth.length':
        'Recumbent length',

      'growth.height':
        'Standing height',

      'growth.head':
        'Head circumference (cm) · optional',

      'growth.oedema':
        'Oedema present',

      'growth.calculate':
        'Calculate growth',

      'growth.results':
        'Growth results',

      'growth.wfa':
        'Weight for age',

      'growth.hfa':
        'Length / height for age',

      'growth.wflh':
        'Weight for length / height',

      'growth.bfa':
        'BMI for age',

      'growth.hcfa':
        'Head circumference for age',

      'growth.z':
        'Z-score',

      'growth.percentile':
        'Percentile',

      'growth.percentileUnavailable':
        'Unavailable outside ±3 SD',

      'growth.who':
        'WHO',

      'growth.brazil':
        'Brazil · SISVAN',

      'growth.noNamedClass':
        'No additional named classification',

      'growth.warning':
        'Notes / warnings',

      'growth.adjustment':
        'Measurement-position adjustment',

      'growth.bmi':
        'Calculated BMI',

      'growth.offline':
        'Result calculated locally using the precached WHO tables.',

      'growth.invalid':
        'Enter sex, a valid age and at least one anthropometric measurement.',

      'growth.positionRequired':
        'Specify whether the measurement was recumbent length or standing height.',

      'growth.source':
        'Numerical references: WHO 2006/2007 · national interpretation: Brazilian Ministry of Health / SISVAN.',

      'growth.noEndorsement':
        'WHO does not endorse this application or its outputs.',

      'growth.attribution':
        'Tables and provenance: assets/reference/who-growth/NOTICE.txt.'
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
