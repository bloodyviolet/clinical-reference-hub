(() => {
  'use strict';

  const ENTRIES =
    Object.freeze({

      1: Object.freeze({
        policy_name:
          'PNAISH',

        directive:
          'Urological Care and Early Diagnosis',

        target_demographic:
          'Men aged 20–59 years',

        clinical_guideline:
          'Care for urinary symptoms, sexual health and urological conditions, including timely investigation of signs and symptoms suspicious for prostate cancer. The Ministry of Health/INCA does not recommend population screening for prostate cancer with PSA and/or digital rectal examination in asymptomatic men; when a user requests screening, risks and benefits should be discussed as part of shared decision-making.'
      }),

      2: Object.freeze({
        policy_name:
          'PNAISH',

        directive:
          'Cardiovascular and Chronic Diseases',

        target_demographic:
          'Adult male population',

        clinical_guideline:
          'Early engagement for primary prevention and treatment of arterial hypertension, ischaemic heart disease and diabetes mellitus.'
      }),

      3: Object.freeze({
        policy_name:
          'PNAISH',

        directive:
          'Prevention of Violence and External Causes',

        target_demographic:
          'Young men (20–39 years)',

        clinical_guideline:
          'Actions to prevent land-transport accidents, assaults and self-inflicted injuries (suicide), which represent the leading cause of mortality in this age group.'
      }),

      4: Object.freeze({
        policy_name:
          'PNAISH',

        directive:
          'Tobacco and Alcohol Control',

        target_demographic:
          'General male population',

        clinical_guideline:
          'Prevention and treatment actions for harmful alcohol and tobacco use, which are strongly associated with male morbidity and mortality, including cirrhosis, accidents and cancer.'
      }),

      5: Object.freeze({
        policy_name:
          'PNAISH',

        directive:
          'Fatherhood and Reproductive Planning',

        target_demographic:
          'Men (adolescents and adults)',

        clinical_guideline:
          'Include men in family-planning actions, encourage responsible fatherhood and ensure access to voluntary vasectomy.'
      }),

      6: Object.freeze({
        policy_name:
          'PNAISH',

        directive:
          'STI/HIV/AIDS Prevention',

        target_demographic:
          'Sexually active men',

        clinical_guideline:
          'Promote condom use and other combined-prevention strategies, with access to testing, diagnosis and treatment for STIs/HIV in accordance with current protocols.'
      }),

      7: Object.freeze({
        policy_name:
          'PNAISC',

        directive:
          'Humanised Pregnancy and Birth Care',

        target_demographic:
          'Pregnant women and newborns',

        clinical_guideline:
          'Promote immediate skin-to-skin contact, delayed cord clamping, the Kangaroo Method for low-birth-weight infants and the “5th Day of Comprehensive Health” in Primary Care.'
      }),

      8: Object.freeze({
        policy_name:
          'PNAISC',

        directive:
          'Breastfeeding and Complementary Feeding',

        target_demographic:
          'Children aged 0–2 years',

        clinical_guideline:
          'Promote exclusive breastfeeding until 6 months of age and continued breastfeeding until 2 years or beyond, with appropriate and healthy complementary feeding from 6 months onwards.'
      }),

      9: Object.freeze({
        policy_name:
          'PNAISC',

        directive:
          'Growth and Development Monitoring',

        target_demographic:
          'Early childhood (0–5 years)',

        clinical_guideline:
          'Monitor neuropsychomotor development and growth using the Child Health Handbook, with particular attention to vulnerable families.'
      }),

      10: Object.freeze({
        policy_name:
          'PNAISC',

        directive:
          'Care for Prevalent Childhood Diseases (IMCI/AIDPI)',

        target_demographic:
          'Children under 5 years',

        clinical_guideline:
          'Provide qualified management of prevalent childhood illnesses, including respiratory, diarrhoeal and nutritional conditions, with micronutrient supplementation only in accordance with current Ministry of Health programmes, age groups and criteria.'
      }),

      11: Object.freeze({
        policy_name:
          'PNAISC',

        directive:
          'Prevention of Violence and Accidents',

        target_demographic:
          'Children aged 0–9 years',

        clinical_guideline:
          'Carry out mandatory notification of violence through the applicable Sinan-Viva workflows and promote a culture of peace and prevention of domestic and road-traffic accidents.'
      }),

      12: Object.freeze({
        policy_name:
          'PNAISC',

        directive:
          'Universal Newborn Screening',

        target_demographic:
          'Newborns',

        clinical_guideline:
          'Ensure newborn screening within the recommended timeframes: the newborn blood-spot test preferably between 48 hours and the 5th day of life; the red-reflex test before discharge or at the first consultation if not previously performed; newborn hearing screening preferably while still in the maternity unit; and pulse-oximetry screening between 24 and 48 hours of life.'
      }),

      13: Object.freeze({
        policy_name:
          'PNAB',

        directive:
          'Welcoming and Unscheduled Care',

        target_demographic:
          'General population',

        clinical_guideline:
          'Receive all users with qualified listening, risk classification and vulnerability assessment, without restricting access.'
      }),

      14: Object.freeze({
        policy_name:
          'PNAB',

        directive:
          'Longitudinality and Care Coordination',

        target_demographic:
          'Registered families',

        clinical_guideline:
          'Provide continuous follow-up of users, management of therapeutic plans and coordination of patient flow across the Health Care Network (RAS).'
      }),

      15: Object.freeze({
        policy_name:
          'PNAB',

        directive:
          'Home Care',

        target_demographic:
          'Patients with mobility limitations',

        clinical_guideline:
          'Provide systematic home visits and home-based care for bedridden patients or patients with stable chronic conditions.'
      }),

      16: Object.freeze({
        policy_name:
          'PNAB',

        directive:
          'Multiprofessional Teams in Primary Health Care (eMulti)',

        target_demographic:
          'Teams and population followed in Primary Health Care',

        clinical_guideline:
          'Provide complementary multiprofessional work integrated with Primary Health Care teams, including matrix support, case discussion, shared consultations, group activities, home-based actions, development of therapeutic plans and intersectoral coordination. eMulti teams were established by Ordinance GM/MS No. 635/2023 as the current strategy for strengthening multiprofessional care in Primary Health Care.'
      }),

      17: Object.freeze({
        policy_name:
          'PNAB',

        directive:
          'Specific Populations (Street Outreach Clinic / Riverside Communities)',

        target_demographic:
          'People experiencing homelessness and riverside populations',

        clinical_guideline:
          'Use mobile teams with flexible schedules to provide comprehensive care to marginalised populations or people who are difficult to reach.'
      }),

      18: Object.freeze({
        policy_name:
          'PNSTT',

        directive:
          'Notification of Occupational Accidents and Diseases (VISAT)',

        target_demographic:
          'Formal and informal workers',

        clinical_guideline:
          'Identify work-related accidents and diseases and notify them through official systems in accordance with the national list and current surveillance workflows, covering both formal and informal workers.'
      }),

      19: Object.freeze({
        policy_name:
          'PNSTT',

        directive:
          'Occupational History',

        target_demographic:
          'Primary Care patients',

        clinical_guideline:
          'Systematically ask about current and previous occupations in every consultation to assess a possible causal relationship between work and illness.'
      }),

      20: Object.freeze({
        policy_name:
          'PNSTT',

        directive:
          'Work-Related Mental Disorders',

        target_demographic:
          'Workers exposed to psychosocial risk',

        clinical_guideline:
          'Identify and manage mental disorders while clinically and occupationally investigating a possible relationship with work factors such as violence, harassment, overload or traumatic events, without assuming causality solely from the reported exposure.'
      }),

      21: Object.freeze({
        policy_name:
          'PNSTT',

        directive:
          'Pesticide Poisoning',

        target_demographic:
          'Rural workers and surrounding populations',

        clinical_guideline:
          'Recognise suspected pesticide poisoning, provide clinical care according to severity, remove the person from exposure when indicated and perform notification and surveillance in accordance with current national workflows.'
      }),

      22: Object.freeze({
        policy_name:
          'PNSTT',

        directive:
          'Pneumoconioses (Silicosis)',

        target_demographic:
          'Construction and mining workers',

        clinical_guideline:
          'Prevent silica exposure, clinically and occupationally investigate pneumoconioses, provide follow-up according to applicable protocols and record or notify the condition and work situation in accordance with applicable legislation.'
      }),

      23: Object.freeze({
        policy_name:
          'PNSPI',

        directive:
          'Multidimensional Assessment (IVCF-20)',

        target_demographic:
          'People aged 60 years or older',

        clinical_guideline:
          'Perform multidimensional assessment of older people, using IVCF-20 when available and appropriate, to identify risk of functional decline, support vulnerability stratification and guide longitudinal, interprofessional care planning.'
      }),

      24: Object.freeze({
        policy_name:
          'PNSPI',

        directive:
          'Falls Prevention',

        target_demographic:
          'Older people',

        clinical_guideline:
          'Assess the home environment, correct visual deficits, review polypharmacy and encourage muscle strengthening and balance.'
      }),

      25: Object.freeze({
        policy_name:
          'PNSPI',

        directive:
          'Polypharmacy Management',

        target_demographic:
          'Older people taking multiple medicines',

        clinical_guideline:
          'Periodically review prescriptions to reduce harmful drug interactions, adverse reactions and increased risk of falls or confusion.'
      }),

      26: Object.freeze({
        policy_name:
          'PNSPI',

        directive:
          'Prevention and Identification of Violence and Abuse',

        target_demographic:
          'Vulnerable older people',

        clinical_guideline:
          'Actively identify neglect, abandonment and physical, psychological or financial abuse and activate the protection network, including Disque 100 and CRAS, when appropriate.'
      }),

      27: Object.freeze({
        policy_name:
          'PNSPI',

        directive:
          'Mental and Cognitive Health',

        target_demographic:
          'Older people',

        clinical_guideline:
          'Screen for and treat depression, social isolation and dementias, including Alzheimer’s disease, while promoting maintenance of autonomy and functional independence.'
      }),

      28: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Sickle Cell Disease and Haemoglobinopathies',

        target_demographic:
          'Black population and people at risk of haemoglobinopathies',

        clinical_guideline:
          'Recognise the historically greater burden of sickle cell disease in the Black population without restricting diagnostic consideration by race or colour. Ensure newborn screening, timely diagnosis, longitudinal follow-up and access to specialist care in accordance with SUS protocols.'
      }),

      29: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Diabetes Mellitus and Health Inequities',

        target_demographic:
          'Black population',

        clinical_guideline:
          'Prevent, screen for and control diabetes according to current clinical criteria, while recognising and addressing access barriers, social determinants and racial inequities that can worsen diagnosis, continuity of care and outcomes.'
      }),

      30: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Arterial Hypertension and Health Inequities',

        target_demographic:
          'Black population',

        clinical_guideline:
          'Prevent, diagnose and control hypertension according to current protocols, with attention to inequities in access, quality of care and blood-pressure control associated with social determinants and structural and institutional racism.'
      }),

      31: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'G6PD Deficiency and Safety of Care',

        target_demographic:
          'People with suspected or possible G6PD deficiency',

        clinical_guideline:
          'Recognise G6PD deficiency as an X-linked genetic condition that can cause haemolysis after certain exposures. Assessment should be clinical and laboratory-based when indicated, without inferring diagnosis solely from race or colour.'
      }),

      32: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Maternal Mortality and Obstetric Care',

        target_demographic:
          'Black pregnant and postpartum women',

        clinical_guideline:
          'Provide timely and qualified antenatal, childbirth and postpartum care, including welcoming care, risk assessment and action against institutional racism; monitor racial inequities in maternal outcomes and ensure rapid access to the referral network.'
      }),

      33: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Mental Health and Substance Use',

        target_demographic:
          'Black population across all age groups',

        clinical_guideline:
          'Strengthen mental-health promotion, prevention and care while considering the effects of racism, discrimination and social exclusion, with non-discriminatory access to the Psychosocial Care Network and to care related to alcohol and other drug use.'
      }),

      34: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'External Causes and Lethal Violence',

        target_demographic:
          'Black population, with particular attention to young people',

        clinical_guideline:
          'Develop violence-prevention and peace-promotion actions, recognise the disproportionate exposure of the Black population—especially young people—to lethal violence and coordinate health, surveillance and social-protection actions without relying on outdated historical statistics.'
      }),

      35: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Communicable Diseases and Equity',

        target_demographic:
          'Black population',

        clinical_guideline:
          'Strengthen prevention, diagnosis, treatment and surveillance of communicable diseases while monitoring racial inequalities in access and outcomes and removing barriers that delay care.'
      }),

      36: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Access for Traditional Communities',

        target_demographic:
          'Quilombola people and peoples or traditional communities of African origin',

        clinical_guideline:
          'Ensure equitable access to SUS actions and services while respecting territory, cultural practices and community knowledge and addressing institutional discrimination in care.'
      }),

      37: Object.freeze({
        policy_name:
          'PNSIPN',

        directive:
          'Monitoring and the Race/Colour Variable',

        target_demographic:
          'SUS managers and health professionals',

        clinical_guideline:
          'Improve recording of the race/colour variable through self-identification in health-information systems and use these data to monitor inequities, plan equity actions and evaluate measures to address institutional racism.'
      }),

      38: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Clinical and Gynaecological Care',

        target_demographic:
          'General female population',

        clinical_guideline:
          'Prevent and treat cardiovascular disease, arterial hypertension and diabetes mellitus, with prioritisation criteria for consultations and tests.'
      }),

      39: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Reproductive Planning',

        target_demographic:
          'Women and men, adults and adolescents',

        clinical_guideline:
          'Ensure access to reversible and surgical contraception, emergency contraception in Primary Care units and infertility care.'
      }),

      40: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Obstetric and Neonatal Care (Rede Alyne)',

        target_demographic:
          'Pregnant and postpartum women',

        clinical_guideline:
          'Organise care through Rede Alyne, with timely enrolment in antenatal care by 12 weeks, at least seven antenatal consultations alternating between nurses and physicians, risk and vulnerability assessment, linkage to the designated maternity service and humanised childbirth and postpartum care.'
      }),

      41: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Abortion and Lawful Abortion Care',

        target_demographic:
          'Women experiencing abortion',

        clinical_guideline:
          'Ensure humanised care before, during and after abortion and access to pregnancy termination in situations permitted by law. For health care related to sexual violence, access to services does not depend on presenting a police report, without prejudice to mandatory health notifications and current care pathways.'
      }),

      42: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Care for Victims of Domestic and Sexual Violence',

        target_demographic:
          'Women and adolescents experiencing violence',

        clinical_guideline:
          'Organise an integrated care network with welcoming care, emergency contraception when indicated, STI/HIV prophylaxis according to protocol and mandatory notification through current official systems.'
      }),

      43: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'STI/HIV/AIDS Prevention and Control',

        target_demographic:
          'Women and pregnant people living with HIV and/or at risk of STIs',

        clinical_guideline:
          'Provide STI/HIV prevention, testing, diagnosis and treatment, with attention to prevention of vertical transmission of HIV and syphilis and access to antiretroviral therapy when indicated under current protocols.'
      }),

      44: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Breast Cancer Screening',

        target_demographic:
          'Women and other people eligible for mammography screening',

        clinical_guideline:
          'Provide routine population mammography screening for women aged 50–74 years every two years. Outside the priority age range, assessment should consider signs and symptoms, individual risk and shared decision-making in accordance with Ministry of Health guidance.'
      }),

      45: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Cervical Cancer Screening',

        target_demographic:
          'Women and other people with a cervix aged 25–64 years who have been sexually active',

        clinical_guideline:
          'Use molecular testing for oncogenic HPV DNA as the primary test in organised screening, at five-year intervals when the result is negative. Cytology remains an alternative where HPV-DNA testing is not yet available, in accordance with current national guidelines.'
      }),

      46: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Mental Health Care with a Gender Perspective',

        target_demographic:
          'Women experiencing psychological distress',

        clinical_guideline:
          'Provide qualified mental-health care throughout the life course, including psychological distress during the perinatal period and climacteric, suicide prevention and access to the Psychosocial Care Network, including CAPS AD when indicated.'
      }),

      47: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Women’s Health Care During the Climacteric',

        target_demographic:
          'Women in the climacteric',

        clinical_guideline:
          'Provide comprehensive care during the climacteric, including health education, promotion of healthy habits and individualised symptom assessment. Pharmacological treatments, including hormone therapy, should be considered only when clinically indicated after assessment of risks, benefits and contraindications.'
      }),

      48: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Health Care for Older Women',

        target_demographic:
          'Older women',

        clinical_guideline:
          'Provide health-promotion actions, prevention of hip fractures, functional-capacity assessment and support for women who are carers.'
      }),

      49: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Health Care for Black Women',

        target_demographic:
          'Black and Quilombola women',

        clinical_guideline:
          'Improve care for sickle cell disease and other relevant conditions, with diagnosis and follow-up according to SUS protocols, while addressing institutional racism and barriers to access in health care.'
      }),

      50: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Health Care for Lesbian and Bisexual Women',

        target_demographic:
          'Lesbian and bisexual women',

        clinical_guideline:
          'Ensure non-discriminatory access to sexual and reproductive health prevention and care, including cancer screening when eligible and STI prevention, without inferring sexual practices from sexual orientation.'
      }),

      51: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Health Care for Rural and Settlement Women Workers',

        target_demographic:
          'Women workers in rural, water and forest communities',

        clinical_guideline:
          'Address health conditions related to rural work, prevent occupational exposures and record or notify conditions through health systems in accordance with current workflows, with guidance on labour and social-security rights when applicable.'
      }),

      52: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Health Care for Indigenous Women',

        target_demographic:
          'Indigenous women',

        clinical_guideline:
          'Provide health actions through local basic-health units coordinated with the Indigenous Special Health Districts (DSEI), while respecting the group’s sociocultural needs.'
      }),

      53: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Health Care for Women in Prison',

        target_demographic:
          'Women in prison',

        clinical_guideline:
          'Ensure comprehensive and humanised pregnancy, childbirth and postpartum care within the prison system. Legislation prohibits shackling during medical or hospital procedures preparatory to childbirth, during labour and in the immediate postpartum period, and also guarantees health care for the pregnant or postpartum woman and the newborn.'
      }),

      54: Object.freeze({
        policy_name:
          'PNAISM',

        directive:
          'Health Care for Women with Disabilities',

        target_demographic:
          'Women with disabilities',

        clinical_guideline:
          'Address health conditions specific to this group and ensure accessibility in reproductive and general clinical health services.'
      })
    });


  function translationFor(
    item
  ) {
    if (
      !item
      || !Number.isInteger(
        Number(
          item.id
        )
      )
    ) {
      return null;
    }

    const translation =
      ENTRIES[
        Number(
          item.id
        )
      ];

    if (
      !translation
      || translation.policy_name
        !== item.policy_name
    ) {
      return null;
    }

    return translation;
  }


  function translateItem(
    item,
    language
  ) {
    if (
      language !== 'en-GB'
    ) {
      return item;
    }

    const translation =
      translationFor(
        item
      );

    if (!translation) {
      return null;
    }

    return {
      ...item,

      directive:
        translation.directive,

      target_demographic:
        translation
          .target_demographic,

      clinical_guideline:
        translation
          .clinical_guideline
    };
  }


  globalThis
    .ClinicalPolicyTranslations =
      Object.freeze({
        language:
          'en-GB',

        count:
          Object.keys(
            ENTRIES
          ).length,

        translationFor,

        translateItem
      });
})();
