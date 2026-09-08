"""Curated public-health policy records and centralized provenance metadata.

Clinical content reviewed 2026-09-07. Keep source overrides close to the row
when a current implementation/guideline supersedes the base policy document.
"""

LAST_CLINICAL_REVIEW = "2026-09-07"

POLICY_SOURCES = {'PNAISH': {'source_title': 'Política Nacional de Atenção Integral à Saúde do Homem (PNAISH) — Anexo XII',
            'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2021/prt3562_15_12_2021.html',
            'source_publication_date': '2021-12-15',
            'source_version': 'Portaria GM/MS nº 3.562/2021',
            'effective_from': '2021-12-15'},
 'PNAISC': {'source_title': 'Política Nacional de Atenção Integral à Saúde da Criança (PNAISC)',
            'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2015/prt1130_05_08_2015.html',
            'source_publication_date': '2015-08-05',
            'source_version': 'Portaria GM/MS nº 1.130/2015',
            'effective_from': '2015-08-05'},
 'PNAB': {'source_title': 'Política Nacional de Atenção Básica (PNAB)',
          'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2017/MatrizesConsolidacao/comum/250584.html',
          'source_publication_date': '2017-09-21',
          'source_version': 'Portaria GM/MS nº 2.436/2017 / Portaria de Consolidação nº 2',
          'effective_from': '2017-09-21'},
 'PNSTT': {'source_title': 'Política Nacional de Saúde do Trabalhador e da Trabalhadora (PNSTT)',
           'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2012/prt1823_23_08_2012.html',
           'source_publication_date': '2012-08-23',
           'source_version': 'Portaria GM/MS nº 1.823/2012',
           'effective_from': '2012-08-23'},
 'PNSPI': {'source_title': 'Política Nacional de Saúde da Pessoa Idosa (PNSPI)',
           'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2006/prt2528_19_10_2006.html',
           'source_publication_date': '2006-10-19',
           'source_version': 'Portaria GM/MS nº 2.528/2006',
           'effective_from': '2006-10-19'},
 'PNSIPN': {'source_title': 'Política Nacional de Saúde Integral da População Negra (PNSIPN)',
            'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2009/prt0992_13_05_2009.html',
            'source_publication_date': '2009-05-13',
            'source_version': 'Portaria GM/MS nº 992/2009',
            'effective_from': '2009-05-13'},
 'PNAISM': {'source_title': 'Política Nacional de Atenção Integral à Saúde da Mulher — Princípios e Diretrizes',
            'source_url': 'https://bvsms.saude.gov.br/bvs/publicacoes/politica_nac_atencao_mulher.pdf',
            'source_publication_date': None,
            'source_version': 'Ministério da Saúde, 2004',
            'effective_from': None}}

SOURCE_OVERRIDES = {'PROSTATE': {'source_title': 'Câncer de próstata — versão para profissionais de saúde (INCA)',
              'source_url': 'https://www.gov.br/inca/pt-br/assuntos/cancer/tipos/prostata/versao-para-profissionais-de-saude',
              'source_publication_date': None,
              'source_version': 'Orientação MS/INCA vigente; rastreamento populacional não recomendado',
              'effective_from': None},
 'BREASTFEEDING': {'source_title': 'Amamentação — Ministério da Saúde',
                   'source_url': 'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/a/aleitamento-materno',
                   'source_publication_date': None,
                   'source_version': 'Orientação vigente do Ministério da Saúde',
                   'effective_from': None},
 'NEONATAL': {'source_title': 'Cuidado Neonatal — Ministério da Saúde',
              'source_url': 'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/saude-da-crianca/cuidado-neonatal',
              'source_publication_date': None,
              'source_version': 'Orientação vigente do Ministério da Saúde',
              'effective_from': None},
 'EMULTI': {'source_title': 'Equipes Multiprofissionais na Atenção Primária à Saúde (eMulti)',
            'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2023/prt0635_22_05_2023.html',
            'source_publication_date': '2023-05-22',
            'source_version': 'Portaria GM/MS nº 635/2023',
            'effective_from': '2023-05-22'},
 'IVCF20': {'source_title': 'Saúde da pessoa idosa — Avaliação multidimensional / IVCF-20',
            'source_url': 'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/saude-da-pessoa-idosa',
            'source_publication_date': None,
            'source_version': 'Implementação atual no e-SUS APS; Nota Informativa nº 2/2025',
            'effective_from': None},
 'REDE_ALYNE': {'source_title': 'Rede Alyne — regulamentação consolidada da atenção materna e infantil',
                'source_url': 'https://bvsms.saude.gov.br/bvs/saudelegis/gm/2026/prt10273_27_02_2026.html',
                'source_publication_date': '2026-02-27',
                'source_version': 'Portaria GM/MS nº 10.273/2026',
                'effective_from': '2026-02-27'},
 'BREAST_CANCER': {'source_title': 'Detecção precoce do câncer de mama — INCA',
                   'source_url': 'https://www.gov.br/inca/pt-br/assuntos/gestor-e-profissional-de-saude/controle-do-cancer-de-mama/acoes/deteccao-precoce',
                   'source_publication_date': None,
                   'source_version': 'Recomendação atualizada em setembro de 2025: 50–74 anos, bienal',
                   'effective_from': '2025-09-01'},
 'PRISON_MATERNITY': {'source_title': 'Lei nº 13.434/2017 — vedação de algemas no parto e puerpério imediato',
                      'source_url': 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13434.htm',
                      'source_publication_date': '2017-04-12',
                      'source_version': 'Lei nº 13.434/2017; complementarmente Lei nº 14.326/2022',
                      'effective_from': '2017-04-13'},
 'ABORTION_LEGAL': {'source_title': 'Violência sexual — acesso aos serviços de saúde e orientação para interrupção gestacional prevista em lei',
                    'source_url': 'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/saude-da-mulher/saude-sexual-e-reprodutiva/violencia-sexual/violencia-sexual',
                    'source_publication_date': None,
                    'source_version': 'Orientação vigente do Ministério da Saúde; acesso aos serviços não depende de boletim de ocorrência',
                    'effective_from': None},
 'CERVICAL': {'source_title': 'Diretrizes Brasileiras para o Rastreamento do Câncer do Colo do Útero — Parte I',
              'source_url': 'https://www.gov.br/saude/pt-br/assuntos/pcdt/r/rastreamento-cancer-do-colo-do-utero/view',
              'source_publication_date': '2025-08-18',
              'source_version': 'DNA-HPV oncogênico como teste primário',
              'effective_from': '2025-08-18'}}

POLICY_DATA = {'PNAISH': [{'directive': 'Atenção Urológica e Diagnóstico Precoce',
             'target_demographic': 'Homens de 20 a 59 anos',
             'clinical_guideline': 'Atenção aos sintomas urinários, saúde sexual e condições urológicas, incluindo investigação oportuna '
                                   'de sinais e sintomas suspeitos de câncer de próstata. O Ministério da Saúde/INCA não recomenda '
                                   'rastreamento populacional de câncer de próstata com PSA e/ou toque retal em homens assintomáticos; '
                                   'quando o usuário solicitar rastreamento, riscos e benefícios devem ser discutidos para decisão '
                                   'compartilhada.',
             '_source_override': 'PROSTATE'},
            {'directive': 'Doenças Cardiovasculares e Crônicas',
             'target_demographic': 'População Masculina Adulta',
             'clinical_guideline': 'Captação precoce para prevenção primária e tratamento de hipertensão arterial, doenças isquêmicas do '
                                   'coração e diabetes mellitus.'},
            {'directive': 'Prevenção de Violência e Causas Externas',
             'target_demographic': 'Homens Jovens (20 a 39 anos)',
             'clinical_guideline': 'Ações de prevenção de acidentes de transporte terrestre, agressões e lesões autoprovocadas (suicídio), '
                                   'que representam a maior causa de mortalidade nesta faixa.'},
            {'directive': 'Controle do Tabagismo e Alcoolismo',
             'target_demographic': 'População Masculina Geral',
             'clinical_guideline': 'Ações de prevenção e tratamento para o uso abusivo de álcool e tabaco, fortemente associados à '
                                   'morbimortalidade masculina (cirrose, acidentes, câncer).'},
            {'directive': 'Paternidade e Planejamento Reprodutivo',
             'target_demographic': 'Homens (Adolescentes e Adultos)',
             'clinical_guideline': 'Inclusão do homem nas ações de planejamento familiar, incentivo à paternidade responsável e garantia '
                                   'de oferta da vasectomia voluntária.'},
            {'directive': 'Prevenção de IST/HIV/aids',
             'target_demographic': 'Homens com Vida Sexual Ativa',
             'clinical_guideline': 'Promoção do uso de preservativos e de outras estratégias de prevenção combinada, com acesso a '
                                   'testagem, diagnóstico e tratamento de IST/HIV conforme protocolos vigentes.'}],
 'PNAISC': [{'directive': 'Atenção Humanizada à Gestação e Nascimento',
             'target_demographic': 'Gestantes e Recém-Nascidos',
             'clinical_guideline': 'Promoção do contato pele a pele imediato, clampeamento tardio do cordão, Método Canguru para baixo '
                                   "peso e '5º Dia de Saúde Integral' na Atenção Básica."},
            {'directive': 'Aleitamento Materno e Alimentação Complementar',
             'target_demographic': 'Crianças de 0 a 2 anos',
             'clinical_guideline': 'Promoção do aleitamento materno exclusivo até os 6 meses e continuado até 2 anos ou mais, com '
                                   'alimentação complementar adequada e saudável a partir dos 6 meses.',
             '_source_override': 'BREASTFEEDING'},
            {'directive': 'Acompanhamento do Crescimento e Desenvolvimento',
             'target_demographic': 'Primeira Infância (0 a 5 anos)',
             'clinical_guideline': 'Vigilância do desenvolvimento neuropsicomotor e crescimento utilizando a Caderneta de Saúde da '
                                   'Criança, com foco em famílias vulneráveis.'},
            {'directive': 'Atenção a Doenças Prevalentes (AIDPI)',
             'target_demographic': 'Crianças menores de 5 anos',
             'clinical_guideline': 'Manejo qualificado de doenças prevalentes na infância, incluindo agravos respiratórios, diarreicos e '
                                   'nutricionais, com suplementação de micronutrientes somente conforme programas, faixas etárias e '
                                   'critérios vigentes do Ministério da Saúde.'},
            {'directive': 'Prevenção de Violências e Acidentes',
             'target_demographic': 'Crianças de 0 a 9 anos',
             'clinical_guideline': 'Notificação compulsória de violências (Sinan-Viva) e ações de promoção da cultura de paz e prevenção '
                                   'de acidentes domésticos e de trânsito.'},
            {'directive': 'Triagens Neonatais Universais',
             'target_demographic': 'Recém-nascidos',
             'clinical_guideline': 'Garantia das triagens neonatais nos tempos recomendados: teste do pezinho preferencialmente entre 48 '
                                   'horas e o 5º dia de vida; teste do olhinho antes da alta ou na primeira consulta se não realizado; '
                                   'teste da orelhinha preferencialmente ainda na maternidade; e teste do coraçãozinho entre 24 e 48 horas '
                                   'de vida.',
             '_source_override': 'NEONATAL'}],
 'PNAB': [{'directive': 'Acolhimento e Demanda Espontânea',
           'target_demographic': 'População em Geral',
           'clinical_guideline': 'Recepção de todos os usuários com escuta qualificada, classificação de risco e avaliação de '
                                 'vulnerabilidade, sem restrição de acesso.'},
          {'directive': 'Longitudinalidade e Coordenação do Cuidado',
           'target_demographic': 'Famílias Adscritas',
           'clinical_guideline': 'Acompanhamento contínuo dos usuários, gerenciamento de projetos terapêuticos e coordenação do fluxo na '
                                 'Rede de Atenção à Saúde (RAS).'},
          {'directive': 'Atenção Domiciliar',
           'target_demographic': 'Pacientes com Dificuldade de Locomoção',
           'clinical_guideline': 'Realização de visitas domiciliares sistemáticas e atenção domiciliar para acamados ou pacientes com '
                                 'problemas crônicos compensados.'},
          {'directive': 'Equipes Multiprofissionais na APS (eMulti)',
           'target_demographic': 'Equipes e população acompanhada na Atenção Primária à Saúde',
           'clinical_guideline': 'Atuação multiprofissional complementar e integrada às equipes da APS, com apoio matricial, discussão de '
                                 'casos, atendimentos compartilhados, atividades coletivas, ações domiciliares, construção de projetos '
                                 'terapêuticos e articulação intersetorial. As eMulti foram instituídas pela Portaria GM/MS nº 635/2023 '
                                 'como estratégia atual de fortalecimento do cuidado multiprofissional na APS.',
           '_source_override': 'EMULTI'},
          {'directive': 'Populações Específicas (Consultório na Rua / Ribeirinhas)',
           'target_demographic': 'População em Situação de Rua e Ribeirinhos',
           'clinical_guideline': 'Equipes itinerantes com horário flexível para prestar atenção integral a populações marginalizadas ou de '
                                 'difícil acesso.'}],
 'PNSTT': [{'directive': 'Notificação de Acidentes e Doenças (Visat)',
            'target_demographic': 'Trabalhadores Formais e Informais',
            'clinical_guideline': 'Identificação de acidentes e doenças relacionadas ao trabalho e notificação nos sistemas oficiais '
                                  'conforme a lista nacional e os fluxos de vigilância vigentes, abrangendo trabalhadores formais e '
                                  'informais.'},
           {'directive': 'Anamnese Ocupacional',
            'target_demographic': 'Pacientes da Atenção Básica',
            'clinical_guideline': 'Inclusão sistemática de perguntas sobre a ocupação atual e pregressa em todas as consultas para '
                                  'estabelecer o nexo causal de adoecimentos.'},
           {'directive': 'Transtornos Mentais Relacionados ao Trabalho',
            'target_demographic': 'Trabalhadores Expostos a Risco Psicossocial',
            'clinical_guideline': 'Identificação e manejo de transtornos mentais, investigando de forma clínica e ocupacional a possível '
                                  'relação com fatores do trabalho, como violência, assédio, sobrecarga ou eventos traumáticos, sem '
                                  'presumir nexo causal apenas pela exposição relatada.'},
           {'directive': 'Intoxicação por Agrotóxicos',
            'target_demographic': 'Trabalhadores Rurais e População do Entorno',
            'clinical_guideline': 'Reconhecimento de suspeitas de intoxicação por agrotóxicos, atendimento clínico conforme gravidade, '
                                  'afastamento da exposição quando indicado e notificação/vigilância conforme os fluxos nacionais '
                                  'vigentes.'},
           {'directive': 'Pneumoconioses (Silicose)',
            'target_demographic': 'Trabalhadores da Construção e Mineração',
            'clinical_guideline': 'Prevenção de exposição à sílica, investigação clínica e ocupacional de pneumoconioses, acompanhamento '
                                  'conforme protocolos e registro/notificação do agravo e da situação de trabalho de acordo com a '
                                  'legislação aplicável.'}],
 'PNSPI': [{'directive': 'Avaliação Multidimensional (IVCF-20)',
            'target_demographic': 'Pessoas com 60 anos ou mais',
            'clinical_guideline': 'Realização de avaliação multidimensional da pessoa idosa, com uso do IVCF-20 quando '
                                  'disponível/adequado, para identificar risco de declínio funcional, apoiar estratificação de '
                                  'vulnerabilidade e orientar plano de cuidados longitudinal e interprofissional.',
            '_source_override': 'IVCF20'},
           {'directive': 'Prevenção de Quedas',
            'target_demographic': 'Pessoas Idosas',
            'clinical_guideline': 'Avaliação ambiental do domicílio, correção de déficits visuais, revisão de polifarmácia e estímulo ao '
                                  'fortalecimento muscular e equilíbrio.'},
           {'directive': 'Manejo da Polifarmácia',
            'target_demographic': 'Idosos em uso de múltiplos medicamentos',
            'clinical_guideline': 'Revisão periódica de prescrições para evitar interações medicamentosas nocivas, reações adversas e '
                                  'risco aumentado de quedas ou confusão mental.'},
           {'directive': 'Prevenção e Identificação de Violências',
            'target_demographic': 'Pessoas Idosas Vulneráveis',
            'clinical_guideline': 'Detecção ativa de negligência, abandono, violência física, psicológica ou patrimonial (financeira) e '
                                  'acionamento da rede de proteção (Disque 100, CRAS).'},
           {'directive': 'Saúde Mental e Cognitiva',
            'target_demographic': 'Pessoas Idosas',
            'clinical_guideline': 'Rastreio e tratamento de depressão, isolamento social, e demências (Alzheimer), promovendo a manutenção '
                                  'da autonomia e independência funcional.'}],
 'PNSIPN': [{'directive': 'Doença Falciforme e Hemoglobinopatias',
             'target_demographic': 'População Negra e pessoas com risco de hemoglobinopatias',
             'clinical_guideline': 'Reconhecer a maior carga histórica da doença falciforme na população negra sem restringir a '
                                   'possibilidade diagnóstica por raça/cor. Garantir triagem neonatal, diagnóstico oportuno, seguimento '
                                   'longitudinal e acesso ao cuidado especializado conforme protocolos do SUS.'},
            {'directive': 'Diabetes Mellitus e Iniquidades em Saúde',
             'target_demographic': 'População Negra',
             'clinical_guideline': 'Prevenir, rastrear e controlar diabetes conforme critérios clínicos vigentes, reconhecendo e '
                                   'enfrentando barreiras de acesso, determinantes sociais e iniquidades raciais que podem piorar '
                                   'diagnóstico, continuidade do cuidado e desfechos.'},
            {'directive': 'Hipertensão Arterial e Iniquidades em Saúde',
             'target_demographic': 'População Negra',
             'clinical_guideline': 'Realizar prevenção, diagnóstico e controle da hipertensão conforme protocolos vigentes, com atenção às '
                                   'iniquidades de acesso, qualidade do cuidado e controle pressórico associadas aos determinantes sociais '
                                   'e ao racismo estrutural e institucional.'},
            {'directive': 'Deficiência de G6PD e Segurança do Cuidado',
             'target_demographic': 'Pessoas com suspeita ou risco de deficiência de G6PD',
             'clinical_guideline': 'Reconhecer a deficiência de G6PD como condição genética ligada ao cromossomo X que pode causar '
                                   'hemólise após determinadas exposições. A avaliação deve ser clínica e laboratorial quando indicada, '
                                   'sem inferir diagnóstico com base apenas em raça/cor.'},
            {'directive': 'Mortalidade Materna e Atenção Obstétrica',
             'target_demographic': 'Gestantes e Puérperas Negras',
             'clinical_guideline': 'Qualificar o pré-natal, o parto e o puerpério com cuidado oportuno, acolhimento, avaliação de risco e '
                                   'enfrentamento do racismo institucional, monitorando iniquidades raciais nos desfechos maternos e '
                                   'garantindo acesso rápido à rede de referência.'},
            {'directive': 'Saúde Mental e Uso de Substâncias',
             'target_demographic': 'População Negra em todas as faixas etárias',
             'clinical_guideline': 'Fortalecer promoção, prevenção e cuidado em saúde mental considerando os impactos do racismo, '
                                   'discriminação e exclusão social, com acesso não discriminatório à Rede de Atenção Psicossocial e ao '
                                   'cuidado relacionado ao uso de álcool e outras drogas.'},
            {'directive': 'Causas Externas e Violência Letal',
             'target_demographic': 'População Negra, com atenção a jovens',
             'clinical_guideline': 'Desenvolver ações de prevenção das violências e promoção da cultura de paz, reconhecer a exposição '
                                   'desproporcional da população negra — especialmente jovens — à violência letal e articular saúde, '
                                   'vigilância e proteção social sem depender de estatísticas históricas desatualizadas.'},
            {'directive': 'Doenças Transmissíveis e Equidade',
             'target_demographic': 'População Negra',
             'clinical_guideline': 'Qualificar prevenção, diagnóstico, tratamento e vigilância de doenças transmissíveis, monitorando '
                                   'desigualdades raciais no acesso e nos desfechos e removendo barreiras que atrasem o cuidado.'},
            {'directive': 'Acesso de Comunidades Tradicionais',
             'target_demographic': 'Quilombolas e povos/comunidades tradicionais de matriz africana',
             'clinical_guideline': 'Garantir acesso equitativo às ações e serviços do SUS, respeitando territorialidade, práticas '
                                   'culturais e saberes comunitários e enfrentando discriminação institucional no cuidado.'},
            {'directive': 'Monitoramento e Quesito Raça/Cor',
             'target_demographic': 'Gestão e profissionais do SUS',
             'clinical_guideline': 'Qualificar o registro do quesito raça/cor por autodeclaração nos sistemas de informação em saúde, '
                                   'utilizando os dados para monitorar iniquidades, planejar ações de equidade e avaliar o enfrentamento '
                                   'do racismo institucional.'}],
 'PNAISM': [{'directive': 'Atenção Clínico-Ginecológica',
             'target_demographic': 'População Feminina Geral',
             'clinical_guideline': 'Prevenção e tratamento de doenças cardiovasculares, hipertensão arterial e diabetes mellitus, com '
                                   'critérios de priorização para consultas e exames.'},
            {'directive': 'Planejamento Reprodutivo',
             'target_demographic': 'Mulheres e Homens, Adultos e Adolescentes',
             'clinical_guideline': 'Garantia de acesso à anticoncepção reversível e cirúrgica, contracepção de emergência nas unidades '
                                   'básicas, e assistência em infertilidade.'},
            {'directive': 'Atenção Obstétrica e Neonatal (Rede Alyne)',
             'target_demographic': 'Gestantes e Puérperas',
             'clinical_guideline': 'Organização do cuidado pela Rede Alyne, com captação oportuna da gestante (até 12 semanas), no mínimo '
                                   'sete consultas de pré-natal intercaladas entre enfermeiros e médicos, avaliação de risco e '
                                   'vulnerabilidade, vinculação à maternidade de referência e atenção humanizada ao parto e puerpério.',
             '_source_override': 'REDE_ALYNE'},
            {'directive': 'Atenção ao Abortamento e Aborto Legal',
             'target_demographic': 'Mulheres em Situação de Abortamento',
             'clinical_guideline': 'Garantia de atendimento humanizado pré, durante e pós-abortamento e de acesso à interrupção gestacional '
                                   'nas situações previstas em lei. Nos atendimentos de saúde relacionados à violência sexual, o acesso aos '
                                   'serviços não depende da apresentação de Boletim de Ocorrência, sem prejuízo das notificações sanitárias '
                                   'obrigatórias e dos fluxos assistenciais vigentes.',
             '_source_override': 'ABORTION_LEGAL'},
            {'directive': 'Atenção às Vítimas de Violência Doméstica e Sexual',
             'target_demographic': 'Mulheres e Adolescentes em Situação de Violência',
             'clinical_guideline': 'Organização de rede integrada com acolhimento, contracepção de emergência quando indicada, profilaxias '
                                   'para IST/HIV conforme protocolo e notificação compulsória pelos sistemas oficiais vigentes.'},
            {'directive': 'Prevenção e Controle de IST/HIV/aids',
             'target_demographic': 'Mulheres e pessoas gestantes vivendo com HIV e/ou com risco de IST',
             'clinical_guideline': 'Prevenção, testagem, diagnóstico e tratamento de IST/HIV, com atenção à prevenção da transmissão '
                                   'vertical do HIV e da sífilis e garantia de terapia antirretroviral quando indicada conforme protocolos '
                                   'vigentes.'},
            {'directive': 'Rastreamento do Câncer de Mama',
             'target_demographic': 'Mulheres e demais pessoas elegíveis ao rastreamento mamográfico',
             'clinical_guideline': 'Rastreamento mamográfico populacional de rotina para mulheres de 50 a 74 anos, a cada dois anos. Fora '
                                   'da faixa prioritária, a avaliação deve considerar sinais/sintomas, risco individual e decisão '
                                   'compartilhada conforme orientação do Ministério da Saúde.',
             '_source_override': 'BREAST_CANCER'},
            {'directive': 'Rastreamento do Câncer do Colo do Útero',
             'target_demographic': 'Mulheres e demais pessoas com colo do útero de 25 a 64 anos que já tiveram atividade sexual',
             'clinical_guideline': 'O teste molecular para DNA-HPV oncogênico é o exame primário no rastreamento organizado, com intervalo '
                                   'de cinco anos quando o resultado é negativo. A citologia permanece como alternativa onde o teste de '
                                   'DNA-HPV ainda não está disponível, conforme diretrizes nacionais vigentes.',
             '_source_override': 'CERVICAL'},
            {'directive': 'Atenção à Saúde Mental com Enfoque de Gênero',
             'target_demographic': 'Mulheres com Sofrimento Psíquico',
             'clinical_guideline': 'Atenção qualificada à saúde mental ao longo do ciclo de vida, incluindo sofrimento psíquico no período '
                                   'perinatal e climatério, prevenção do suicídio e acesso à Rede de Atenção Psicossocial, inclusive CAPS '
                                   'AD quando indicado.'},
            {'directive': 'Atenção à Saúde da Mulher no Climatério',
             'target_demographic': 'Mulheres no Climatério',
             'clinical_guideline': 'Atenção integral no climatério com educação em saúde, promoção de hábitos saudáveis e avaliação '
                                   'individualizada dos sintomas. Tratamentos farmacológicos, inclusive terapia hormonal, devem ser '
                                   'considerados apenas quando clinicamente indicados após avaliação de riscos, benefícios e '
                                   'contraindicações.'},
            {'directive': 'Atenção à Saúde das Mulheres Idosas',
             'target_demographic': 'Mulheres Idosas',
             'clinical_guideline': 'Ações de promoção da saúde, prevenção de fraturas de fêmur, avaliação de capacidade funcional e apoio '
                                   'a mulheres cuidadoras.'},
            {'directive': 'Atenção à Saúde das Mulheres Negras',
             'target_demographic': 'Mulheres Negras e Quilombolas',
             'clinical_guideline': 'Qualificação do cuidado para doença falciforme e outras condições relevantes, com diagnóstico e '
                                   'seguimento conforme protocolos do SUS, além do enfrentamento ao racismo institucional e às barreiras '
                                   'de acesso no atendimento.'},
            {'directive': 'Atenção à Saúde das Mulheres Lésbicas e Bissexuais',
             'target_demographic': 'Mulheres Lésbicas e Bissexuais',
             'clinical_guideline': 'Garantia de acesso não discriminatório à prevenção e ao cuidado em saúde sexual e reprodutiva, '
                                   'incluindo rastreamento de câncer quando elegível e prevenção de IST, sem pressupor práticas sexuais a '
                                   'partir da orientação sexual.'},
            {'directive': 'Atenção à Saúde das Trabalhadoras Rurais e Assentadas',
             'target_demographic': 'Mulheres Trabalhadoras do Campo, Águas e Floresta',
             'clinical_guideline': 'Atenção aos agravos relacionados ao trabalho rural, prevenção de exposições ocupacionais e '
                                   'registro/notificação nos sistemas de saúde conforme os fluxos vigentes, com orientação sobre direitos '
                                   'trabalhistas e previdenciários quando aplicável.'},
            {'directive': 'Atenção à Saúde das Mulheres Indígenas',
             'target_demographic': 'Mulheres Indígenas',
             'clinical_guideline': 'Ações de saúde nos polos básicos articuladas com os Distritos Sanitários Especiais Indígenas (DSEI), '
                                   'respeitando as demandas socioculturais do grupo.'},
            {'directive': 'Atenção à Saúde das Mulheres Privadas de Liberdade',
             'target_demographic': 'Mulheres em Situação de Prisão',
             'clinical_guideline': 'Garantia de atenção integral e humanizada à gestação, parto e puerpério no sistema prisional. A '
                                   'legislação veda algemas durante atos médico-hospitalares preparatórios para o parto, durante o '
                                   'trabalho de parto e no puerpério imediato, além de assegurar assistência à saúde da gestante/puérpera '
                                   'e do recém-nascido.',
             '_source_override': 'PRISON_MATERNITY'},
            {'directive': 'Atenção à Saúde das Mulheres com Deficiência',
             'target_demographic': 'Mulheres com Deficiência',
             'clinical_guideline': 'Ações voltadas aos agravos específicos do grupo e garantia de acessibilidade nos serviços de saúde '
                                   'reprodutiva e clínica.'}]}


# Human-readable locator for sources that are current web guidance or a specific
# amending/legal instrument rather than the base policy PDF.
OVERRIDE_LOCATORS = {
    "PROSTATE": "INCA — seção de detecção precoce/rastreamento para profissionais",
    "BREASTFEEDING": "Ministério da Saúde — orientação vigente de aleitamento materno",
    "NEONATAL": "Ministério da Saúde — Cuidado Neonatal / triagens neonatais",
    "EMULTI": "Portaria GM/MS nº 635/2023 — instituição e atuação das eMulti",
    "IVCF20": "Ministério da Saúde — avaliação multidimensional da pessoa idosa / IVCF-20",
    "REDE_ALYNE": "Portaria GM/MS nº 10.273/2026 — regulamentação consolidada da Rede Alyne",
    "BREAST_CANCER": "INCA — detecção precoce / rastreamento mamográfico",
    "PRISON_MATERNITY": "CPP, art. 292, parágrafo único (Lei nº 13.434/2017)",
    "ABORTION_LEGAL": "Ministério da Saúde — Violência sexual: etapas/acesso aos serviços",
    "CERVICAL": "Diretrizes Brasileiras 2025 — rastreamento primário por DNA-HPV",
}

# Pinpoint locators identify where the base policy directly supports each summarized
# directive. A current implementation override takes precedence over these locators.
POLICY_LOCATORS = {
    # PNAISH — Portaria GM/MS 3.562/2021, Anexo XII
    ("PNAISH", "Doenças Cardiovasculares e Crônicas"): "Anexo XII, art. 4º, V; art. 5º, IV",
    ("PNAISH", "Prevenção de Violência e Causas Externas"): "Anexo XII, art. 4º, XVI; art. 5º, V",
    ("PNAISH", "Controle do Tabagismo e Alcoolismo"): "Anexo XII, art. 4º, XI; art. 5º, IV-V",
    ("PNAISH", "Paternidade e Planejamento Reprodutivo"): "Anexo XII, art. 4º, XIII e XV; art. 5º, II-III",
    ("PNAISH", "Prevenção de IST/HIV/aids"): "Anexo XII, art. 4º, XII e XIV; art. 5º, II",

    # PNAISC — Portaria GM/MS 1.130/2015
    ("PNAISC", "Atenção Humanizada à Gestação e Nascimento"): "art. 6º, I; art. 7º",
    ("PNAISC", "Acompanhamento do Crescimento e Desenvolvimento"): "art. 6º, III; art. 9º, I-II",
    ("PNAISC", "Atenção a Doenças Prevalentes (AIDPI)"): "art. 6º, IV; art. 10, I-III",
    ("PNAISC", "Prevenção de Violências e Acidentes"): "art. 6º, V; art. 11",

    # PNAB — Portaria 2.436/2017 / Consolidação nº 2, Anexo XXII
    ("PNAB", "Acolhimento e Demanda Espontânea"): "Anexo XXII — diretrizes/atribuições comuns: acolhimento, risco e vulnerabilidade",
    ("PNAB", "Longitudinalidade e Coordenação do Cuidado"): "Anexo XXII — diretrizes: longitudinalidade e coordenação do cuidado",
    ("PNAB", "Atenção Domiciliar"): "Anexo XXII — atribuições da APS e atenção no domicílio",
    ("PNAB", "Populações Específicas (Consultório na Rua / Ribeirinhas)"): "Anexo XXII — modalidades/equipes para populações específicas",

    # PNSTT — Portaria GM/MS 1.823/2012
    ("PNSTT", "Notificação de Acidentes e Doenças (Visat)"): "art. 9º, I; art. 13, X",
    ("PNSTT", "Anamnese Ocupacional"): "art. 8º, V-VI; art. 9º, I",
    ("PNSTT", "Transtornos Mentais Relacionados ao Trabalho"): "art. 8º, III e VI; art. 9º, I e VI",
    ("PNSTT", "Intoxicação por Agrotóxicos"): "art. 8º, III e VI; art. 9º, I e VI",
    ("PNSTT", "Pneumoconioses (Silicose)"): "art. 8º, III e VI; art. 9º, I e VI",

    # PNSPI — Portaria GM/MS 2.528/2006
    ("PNSPI", "Prevenção de Quedas"): "Anexo, item 3.1(e) e item 3.2",
    ("PNSPI", "Manejo da Polifarmácia"): "Anexo, item 3.2 — avaliação integral e manejo de medicamentos",
    ("PNSPI", "Prevenção e Identificação de Violências"): "Anexo, item 3.1(f) e item 3.2",
    ("PNSPI", "Saúde Mental e Cognitiva"): "Anexo, item 3.2 — avaliação cognitiva, humor/depressão e funcionalidade",

    # PNSIPN — Portaria GM/MS 992/2009
    ("PNSIPN", "Doença Falciforme e Hemoglobinopatias"): "Anexo, Cap. III, VIII",
    ("PNSIPN", "Mortalidade Materna e Atenção Obstétrica"): "Anexo, Cap. III, II e VII",
    ("PNSIPN", "Saúde Mental e Uso de Substâncias"): "Anexo, Cap. III, V-VI",
    ("PNSIPN", "Causas Externas e Violência Letal"): "Anexo, Cap. III, II e XI",
    ("PNSIPN", "Doenças Transmissíveis e Equidade"): "Anexo, Cap. III, II",
    ("PNSIPN", "Acesso de Comunidades Tradicionais"): "Anexo, Cap. II, objetivo específico II; Cap. III, IV",
    ("PNSIPN", "Monitoramento e Quesito Raça/Cor"): "Anexo, Cap. II, objetivos V-VI; Cap. III, IX",
    ("PNSIPN", "Diabetes Mellitus e Iniquidades em Saúde"): "Anexo, Cap. I-II — determinantes, equidade e monitoramento; condição não nomeada como diretriz autônoma",
    ("PNSIPN", "Hipertensão Arterial e Iniquidades em Saúde"): "Anexo, Cap. I-II — determinantes, equidade e monitoramento; condição não nomeada como diretriz autônoma",
    ("PNSIPN", "Deficiência de G6PD e Segurança do Cuidado"): "Anexo, Cap. I-II — equidade/qualidade do cuidado; condição não nomeada como diretriz autônoma",

    # PNAISM — Política Nacional de Atenção Integral à Saúde da Mulher, 2004
    ("PNAISM", "Atenção Clínico-Ginecológica"): "p. 69 — objetivos específicos e estratégias",
    ("PNAISM", "Planejamento Reprodutivo"): "p. 69 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção às Vítimas de Violência Doméstica e Sexual"): "p. 70 — objetivos específicos e estratégias",
    ("PNAISM", "Prevenção e Controle de IST/HIV/aids"): "p. 70 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção à Saúde Mental com Enfoque de Gênero"): "p. 71 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção à Saúde da Mulher no Climatério"): "p. 71 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção à Saúde das Mulheres Idosas"): "p. 71 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção à Saúde das Mulheres Negras"): "pp. 71-72 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção à Saúde das Mulheres Lésbicas e Bissexuais"): "pp. 63-64 — princípios e diretrizes sobre grupos/orientações sexuais",
    ("PNAISM", "Atenção à Saúde das Trabalhadoras Rurais e Assentadas"): "p. 72 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção à Saúde das Mulheres Indígenas"): "p. 72 — objetivos específicos e estratégias",
    ("PNAISM", "Atenção à Saúde das Mulheres com Deficiência"): "pp. 63-64 — princípios e diretrizes sobre grupos específicos",
}

# These records are useful equity/clinical-context prompts, but the named condition is
# not itself an explicit core directive of the cited base policy. Keep that distinction
# machine-readable rather than overstating source precision.
POLICY_CONTEXT_ROWS = {
    ("PNAISH", "Controle do Tabagismo e Alcoolismo"),
    ("PNSIPN", "Diabetes Mellitus e Iniquidades em Saúde"),
    ("PNSIPN", "Hipertensão Arterial e Iniquidades em Saúde"),
    ("PNSIPN", "Deficiência de G6PD e Segurança do Cuidado"),
}

def iter_policy_records(policy_names=None):
    selected = set(policy_names) if policy_names else None
    for policy_name, rows in POLICY_DATA.items():
        if selected is not None and policy_name not in selected:
            continue
        base_source = POLICY_SOURCES[policy_name]
        for raw in rows:
            row = dict(raw)
            override_key = row.pop("_source_override", None)
            source = dict(base_source)
            if override_key:
                source.update(SOURCE_OVERRIDES[override_key])

            key = (policy_name, row["directive"])
            locator = row.get("source_page") or (OVERRIDE_LOCATORS.get(override_key) if override_key else None) or POLICY_LOCATORS.get(key)
            if override_key:
                evidence_level = "current_override"
                default_review_note = "Current implementation/guideline override independently sourced during the 2026-09-07 review."
            elif key in POLICY_CONTEXT_ROWS:
                evidence_level = "policy_context"
                default_review_note = "Condition-specific wording is an equity/clinical-context interpretation; the named condition is not an explicit standalone directive in the base policy."
            elif locator:
                evidence_level = "pinpoint_policy"
                default_review_note = "Direct supporting section/article/page located in the base policy during the 2026-09-07 review."
            else:
                evidence_level = "policy_level"
                default_review_note = "Policy-level provenance retained; additional pinpoint verification is still recommended before treating this summary as verbatim policy guidance."

            yield {
                "policy_name": policy_name,
                "directive": row["directive"],
                "target_demographic": row["target_demographic"],
                "clinical_guideline": row["clinical_guideline"],
                **source,
                "source_page": locator,
                "last_clinical_review": LAST_CLINICAL_REVIEW,
                "status": row.get("status", "current"),
                "review_notes": row.get("review_notes", default_review_note),
                "effective_until": row.get("effective_until"),
                "evidence_level": row.get("evidence_level", evidence_level),
            }
