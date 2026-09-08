from __future__ import annotations

import csv
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.clinical_content import validate_guidance_content
CSV_PATH = ROOT / "sae_bilingual_final.csv"
META_PATH = ROOT / "data" / "nanda_2024_2026_metadata.json"
GUIDANCE_PATH = ROOT / "data" / "f02_f03_candidate_patch.json"
REVIEW_DATE = "2026-09-08"
NANDA_EDITION = "NANDA-I 2024-2026, 13th edition"
NIC_EDITION = "Nursing Interventions Classification (NIC), 8th edition"
NOC_EDITION = "Nursing Outcomes Classification (NOC), 7th edition"

# Labels below are intentionally short classification labels only. The API's activity/evaluation
# prose is locally authored and is not a reproduction of classification definitions/activities.
NIC = {
    "0180": ("Energy Management", "Controle de Energia"),
    "0200": ("Exercise Promotion", "Promoção do Exercício"),
    "0221": ("Exercise Therapy: Ambulation", "Terapia com Exercício: Deambulação"),
    "0410": ("Bowel Incontinence Care", "Cuidados na Incontinência Intestinal"),
    "0430": ("Bowel Management", "Controle Intestinal"),
    "0450": ("Constipation/Impaction Management", "Controle da Constipação/Impactação"),
    "0590": ("Urinary Elimination Management", "Controle da Eliminação Urinária"),
    "0610": ("Urinary Incontinence Care", "Cuidados na Incontinência Urinária"),
    "0620": ("Urinary Retention Care", "Cuidados na Retenção Urinária"),
    "0840": ("Positioning", "Posicionamento"),
    "0842": ("Positioning: Intraoperative", "Posicionamento: Intraoperatório"),
    "0846": ("Positioning: Wheelchair", "Posicionamento: Cadeira de Rodas"),
    "0970": ("Transfer", "Transferência"),
    "1050": ("Feeding", "Alimentação"),
    "1100": ("Nutrition Management", "Controle da Nutrição"),
    "1160": ("Nutritional Monitoring", "Monitoração Nutricional"),
    "1240": ("Weight Gain Assistance", "Assistência no Ganho de Peso"),
    "1260": ("Weight Management", "Controle do Peso"),
    "1280": ("Weight Reduction Assistance", "Assistência na Redução de Peso"),
    "1350": ("Dry Eye Prevention", "Prevenção de Olho Seco"),
    "1400": ("Pain Management", "Controle da Dor"),
    "1450": ("Nausea Management", "Controle da Náusea"),
    "1650": ("Eye Care", "Cuidados com os Olhos"),
    "1710": ("Oral Health Maintenance", "Manutenção da Saúde Oral"),
    "1720": ("Oral Health Promotion", "Promoção da Saúde Oral"),
    "1800": ("Self-Care Assistance", "Assistência no Autocuidado"),
    "1801": ("Self-Care Assistance: Bathing/Hygiene", "Assistência no Autocuidado: Banho/Higiene"),
    "1802": ("Self-Care Assistance: Dressing/Grooming", "Assistência no Autocuidado: Vestir-se/Arrumar-se"),
    "1803": ("Self-Care Assistance: Feeding", "Assistência no Autocuidado: Alimentação"),
    "1804": ("Self-Care Assistance: Toileting", "Assistência no Autocuidado: Uso do Banheiro"),
    "1850": ("Sleep Enhancement", "Melhora do Sono"),
    "1860": ("Swallowing Therapy", "Terapia para Deglutição"),
    "2080": ("Fluid/Electrolyte Management", "Controle de Líquidos/Eletrólitos"),
    "2620": ("Neurologic Monitoring", "Monitoração Neurológica"),
    "2660": ("Peripheral Sensation Management", "Controle da Sensibilidade Periférica"),
    "2870": ("Postanesthesia Care", "Cuidados Pós-Anestesia"),
    "3200": ("Aspiration Precautions", "Precauções contra Aspiração"),
    "3140": ("Airway Management", "Controle de Vias Aéreas"),
    "3250": ("Cough Enhancement", "Melhora da Tosse"),
    "3350": ("Respiratory Monitoring", "Monitoração Respiratória"),
    "3390": ("Ventilation Assistance", "Assistência Ventilatória"),
    "3520": ("Pressure Injury Care", "Cuidados com Lesão por Pressão"),
    "3540": ("Pressure Injury Prevention", "Prevenção de Lesão por Pressão"),
    "3590": ("Skin Surveillance", "Supervisão da Pele"),
    "3660": ("Wound Care", "Cuidados com Feridas"),
    "3900": ("Temperature Regulation", "Regulação da Temperatura"),
    "4010": ("Bleeding Precautions", "Precauções contra Sangramento"),
    "4040": ("Cardiac Care", "Cuidados Cardíacos"),
    "4050": ("Cardiac Risk Management", "Manejo do Risco Cardíaco"),
    "4062": ("Circulatory Care: Arterial Insufficiency", "Cuidados Circulatórios: Insuficiência Arterial"),
    "4120": ("Fluid Management", "Controle de Líquidos"),
    "4130": ("Fluid Monitoring", "Monitoração de Líquidos"),
    "4150": ("Hemodynamic Regulation", "Regulação Hemodinâmica"),
    "4250": ("Shock Management", "Controle do Choque"),
    "4360": ("Behavior Modification", "Modificação do Comportamento"),
    "4370": ("Impulse Control Training", "Treinamento para Controle de Impulsos"),
    "4480": ("Self-Responsibility Facilitation", "Facilitação da Autorresponsabilidade"),
    "4510": ("Substance Use Treatment", "Tratamento do Uso de Substâncias"),
    "4512": ("Substance Use Treatment: Alcohol Withdrawal", "Tratamento do Uso de Substâncias: Abstinência de Álcool"),
    "4514": ("Substance Use Treatment: Drug Withdrawal", "Tratamento do Uso de Substâncias: Abstinência de Drogas"),
    "4720": ("Cognitive Stimulation", "Estimulação Cognitiva"),
    "4760": ("Memory Training", "Treinamento da Memória"),
    "4820": ("Reality Orientation", "Orientação para a Realidade"),
    "4976": ("Communication Enhancement: Speech Deficit", "Melhora da Comunicação: Déficit da Fala"),
    "5100": ("Socialization Enhancement", "Melhora da Socialização"),
    "5220": ("Body Image Enhancement", "Melhora da Imagem Corporal"),
    "5230": ("Coping Enhancement", "Melhora do Enfrentamento"),
    "5240": ("Counseling", "Aconselhamento"),
    "5244": ("Breastfeeding Counselling", "Aconselhamento sobre Amamentação"),
    "5248": ("Sexual Counseling", "Aconselhamento Sexual"),
    "5250": ("Decision-Making Support", "Apoio à Tomada de Decisão"),
    "5270": ("Emotional Support", "Apoio Emocional"),
    "5290": ("Grief Work Facilitation", "Facilitação do Processo de Luto"),
    "5310": ("Hope Inspiration", "Inspiração de Esperança"),
    "5330": ("Mood Management", "Controle do Humor"),
    "5350": ("Relocation Stress Reduction", "Redução do Estresse por Mudança"),
    "5360": ("Recreational Therapy", "Terapia Recreacional"),
    "5370": ("Role Enhancement", "Melhora do Papel"),
    "5390": ("Self-Awareness Enhancement", "Melhora da Autoconsciência"),
    "5395": ("Self-Efficacy Enhancement", "Melhora da Autoeficácia"),
    "5400": ("Self-Esteem Enhancement", "Melhora da Autoestima"),
    "5420": ("Spiritual Support", "Apoio Espiritual"),
    "5440": ("Support System Enhancement", "Melhora do Sistema de Apoio"),
    "5465": ("Therapeutic Touch", "Toque Terapêutico"),
    "5480": ("Values Clarification", "Esclarecimento de Valores"),
    "5510": ("Health Education", "Educação em Saúde"),
    "5515": ("Health Literacy Enhancement", "Melhora da Literacia em Saúde"),
    "5602": ("Teaching: Disease Process", "Ensino: Processo da Doença"),
    "5650": ("Teaching: Middle Childhood Development (6-12 Years)", "Ensino: Desenvolvimento na Infância Média (6-12 Anos)"),
    "5670": ("Teaching: Adolescent Development (12-21 Years)", "Ensino: Desenvolvimento do Adolescente (12-21 Anos)"),
    "5680": ("Teaching: Early Childhood Development (1-5 Years)", "Ensino: Desenvolvimento na Primeira Infância (1-5 Anos)"),
    "5820": ("Anxiety Reduction", "Redução da Ansiedade"),
    "6340": ("Suicide Prevention", "Prevenção do Suicídio"),
    "6400": ("Abuse Protection Support", "Apoio à Proteção contra Abuso"),
    "6410": ("Allergy Management", "Controle de Alergias"),
    "6440": ("Delirium Management", "Controle do Delirium"),
    "6460": ("Dementia Management", "Controle da Demência"),
    "6482": ("Environmental Management: Comfort", "Controle do Ambiente: Conforto"),
    "6487": ("Environmental Management: Violence Prevention", "Controle do Ambiente: Prevenção da Violência"),
    "6490": ("Fall Prevention", "Prevenção de Quedas"),
    "6540": ("Infection Control", "Controle de Infecção"),
    "6550": ("Infection Protection", "Proteção contra Infecção"),
    "6570": ("Latex Precautions", "Precauções com Látex"),
    "6610": ("Risk Identification", "Identificação de Risco"),
    "6760": ("Childbirth Preparation", "Preparação para o Parto"),
    "6771": ("Electronic Fetal Monitoring: Antepartum", "Monitorização Fetal Eletrônica: Anteparto"),
    "6772": ("Electronic Fetal Monitoring: Intrapartum", "Monitorização Fetal Eletrônica: Intraparto"),
    "6800": ("High-Risk Pregnancy Care", "Cuidados na Gestação de Alto Risco"),
    "6824": ("Infant Care: Newborn", "Cuidados com o Lactente: Recém-Nascido"),
    "6830": ("Intrapartum Care", "Cuidados Intraparto"),
    "6834": ("Intrapartum Care: High-Risk Delivery", "Cuidados Intraparto: Parto de Alto Risco"),
    "6930": ("Postpartum Care", "Cuidados Pós-Parto"),
    "6960": ("Prenatal Care", "Cuidados Pré-Natais"),
    "6924": ("Phototherapy: Neonate", "Fototerapia: Neonato"),
    "7040": ("Caregiver Support", "Apoio ao Cuidador"),
    "7100": ("Family Integrity Promotion", "Promoção da Integridade Familiar"),
    "7104": ("Family Integrity Promotion: Childbearing Family", "Promoção da Integridade Familiar: Família em Processo de Gestação/Nascimento"),
    "7110": ("Family Involvement Promotion", "Promoção do Envolvimento Familiar"),
    "7140": ("Family Support", "Apoio Familiar"),
    "7180": ("Home Maintenance Assistance", "Assistência na Manutenção do Lar"),
    "8250": ("Developmental Care", "Cuidado Desenvolvimental"),
    "8274": ("Child Care", "Cuidados com a Criança"),
    "8278": ("Developmental Enhancement: Infant", "Melhora do Desenvolvimento: Lactente"),
    "8300": ("Parenting Promotion", "Promoção da Parentalidade"),
    "8340": ("Resilience Promotion", "Promoção da Resiliência"),
    "8500": ("Community Health Development", "Desenvolvimento da Saúde Comunitária"),
}

NOC = {
    "0002": ("Energy Conservation", "Conservação de Energia"),
    "0004": ("Sleep", "Sono"),
    "0005": ("Activity Tolerance", "Tolerância à Atividade"),
    "0007": ("Fatigue Level", "Nível de Fadiga"),
    "0100": ("Child Development: 2 Months", "Desenvolvimento Infantil: 2 Meses"),
    "0101": ("Child Development: 4 Months", "Desenvolvimento Infantil: 4 Meses"),
    "0102": ("Child Development: 6 Months", "Desenvolvimento Infantil: 6 Meses"),
    "0103": ("Child Development: 12 Months", "Desenvolvimento Infantil: 12 Meses"),
    "0120": ("Child Development: 1 Month", "Desenvolvimento Infantil: 1 Mês"),
    "0125": ("Child Development: 9 Months", "Desenvolvimento Infantil: 9 Meses"),
    "0126": ("Child Development: 18 Months", "Desenvolvimento Infantil: 18 Meses"),
    "0107": ("Child Development: 5 Years", "Desenvolvimento Infantil: 5 Anos"),
    "0127": ("Child Development: 6-7 Years", "Desenvolvimento Infantil: 6-7 Anos"),
    "0128": ("Child Development: 8-10 Years", "Desenvolvimento Infantil: 8-10 Anos"),
    "0129": ("Child Development: Early Adolescence", "Desenvolvimento Infantil: Adolescência Inicial"),
    "0131": ("Child Development: Middle Adolescence", "Desenvolvimento Infantil: Adolescência Média"),
    "0130": ("Child Development: Late Adolescence", "Desenvolvimento Infantil: Adolescência Tardia"),
    "0110": ("Growth", "Crescimento"),
    "0111": ("Fetal Status: Prenatal", "Estado Fetal: Pré-Natal"),
    "0112": ("Fetal Status: Intrapartum", "Estado Fetal: Durante o Parto"),
    "0113": ("Physical Aging", "Envelhecimento Físico"),
    "0118": ("Newborn Adaptation", "Adaptação do Recém-Nascido"),
    "0117": ("Preterm Infant Organization", "Organização do Lactente Prematuro"),
    "0119": ("Sexual Functioning", "Funcionamento Sexual"),
    "0200": ("Ambulation", "Deambulação"),
    "0204": ("Immobility Consequences: Physiological", "Consequências da Imobilidade: Fisiológicas"),
    "0208": ("Mobility", "Mobilidade"),
    "0300": ("Self-Care Behavior: Activities of Daily Living", "Comportamento de Autocuidado: Atividades de Vida Diária"),
    "0301": ("Self-Care Behavior: Bathing", "Comportamento de Autocuidado: Banho"),
    "0302": ("Self-Care Behavior: Dressing", "Comportamento de Autocuidado: Vestir-se"),
    "0303": ("Self-Care Behavior: Eating", "Comportamento de Autocuidado: Alimentação"),
    "0305": ("Self-Care Behavior: Hygiene", "Comportamento de Autocuidado: Higiene"),
    "0306": ("Self-Care Behavior: Instrumental Activities of Daily Living", "Comportamento de Autocuidado: Atividades Instrumentais de Vida Diária"),
    "0308": ("Self-Care Behavior: Oral Hygiene", "Comportamento de Autocuidado: Higiene Oral"),
    "0310": ("Self-Care Behavior: Toileting", "Comportamento de Autocuidado: Uso do Banheiro"),
    "0400": ("Cardiac Pump Effectiveness", "Eficácia da Bomba Cardíaca"),
    "0401": ("Circulation Status", "Estado Circulatório"),
    "0402": ("Respiratory Status: Gas Exchange", "Estado Respiratório: Troca Gasosa"),
    "0403": ("Respiratory Status: Ventilation", "Estado Respiratório: Ventilação"),
    "0406": ("Tissue Perfusion: Cerebral", "Perfusão Tissular: Cerebral"),
    "0407": ("Tissue Perfusion: Peripheral", "Perfusão Tissular: Periférica"),
    "0410": ("Respiratory Status: Airway Patency", "Estado Respiratório: Permeabilidade das Vias Aéreas"),
    "0412": ("Mechanical Ventilation Weaning Response: Adult", "Resposta ao Desmame da Ventilação Mecânica: Adulto"),
    "0413": ("Blood Loss Severity", "Gravidade da Perda de Sangue"),
    "0414": ("Cardiopulmonary Function", "Função Cardiopulmonar"),
    "0422": ("Tissue Perfusion", "Perfusão Tissular"),
    "0500": ("Bowel Continence", "Continência Intestinal"),
    "0501": ("Bowel Elimination", "Eliminação Intestinal"),
    "0502": ("Urinary Continence", "Continência Urinária"),
    "0503": ("Urinary Elimination", "Eliminação Urinária"),
    "0600": ("Electrolyte and Acid/Base Balance", "Equilíbrio Eletrolítico e Ácido-Base"),
    "0601": ("Fluid Balance", "Equilíbrio Hídrico"),
    "0602": ("Hydration", "Hidratação"),
    "0603": ("Fluid Overload Severity", "Gravidade da Sobrecarga Hídrica"),
    "0606": ("Electrolyte Balance", "Equilíbrio Eletrolítico"),
    "0702": ("Immune Status", "Estado Imunológico"),
    "0703": ("Infection Severity", "Gravidade da Infecção"),
    "0707": ("Immune Hypersensitivity Response", "Resposta de Hipersensibilidade Imunológica"),
    "0800": ("Thermoregulation", "Termorregulação"),
    "0802": ("Vital Signs", "Sinais Vitais"),
    "0900": ("Cognition", "Cognição"),
    "0901": ("Cognitive Orientation", "Orientação Cognitiva"),
    "0902": ("Communication", "Comunicação"),
    "0906": ("Decision-Making", "Tomada de Decisão"),
    "0908": ("Memory", "Memória"),
    "0910": ("Neurological Function: Autonomic", "Função Neurológica: Autonômica"),
    "0917": ("Neurological Status: Peripheral", "Estado Neurológico: Periférico"),
    "1000": ("Breastfeeding Establishment: Infant", "Estabelecimento da Amamentação: Lactente"),
    "1001": ("Breastfeeding Establishment: Maternal", "Estabelecimento da Amamentação: Materno"),
    "1002": ("Breastfeeding Maintenance", "Manutenção da Amamentação"),
    "1004": ("Nutritional Status", "Estado Nutricional"),
    "1008": ("Nutritional Status: Food and Fluid Intake", "Estado Nutricional: Ingestão de Alimentos e Líquidos"),
    "1010": ("Swallowing Status", "Estado da Deglutição"),
    "1015": ("Gastrointestinal Function", "Função Gastrointestinal"),
    "1100": ("Oral Health", "Saúde Oral"),
    "1101": ("Tissue Integrity: Skin & Mucous Membranes", "Integridade Tissular: Pele e Mucosas"),
    "1102": ("Wound Healing: Primary Intention", "Cicatrização de Feridas: Primeira Intenção"),
    "1103": ("Wound Healing: Secondary Intention", "Cicatrização de Feridas: Segunda Intenção"),
    "1200": ("Body Image", "Imagem Corporal"),
    "1201": ("Hope", "Esperança"),
    "1203": ("Loneliness Severity", "Gravidade da Solidão"),
    "1204": ("Mood Equilibrium", "Equilíbrio do Humor"),
    "1205": ("Self-Esteem", "Autoestima"),
    "1210": ("Fear Level", "Nível de Medo"),
    "1211": ("Anxiety Level", "Nível de Ansiedade"),
    "1212": ("Stress Level", "Nível de Estresse"),
    "1302": ("Coping", "Enfrentamento"),
    "1304": ("Grief Resolution", "Resolução do Luto"),
    "1305": ("Psychosocial Adjustment: Life Change", "Ajuste Psicossocial: Mudança de Vida"),
    "1309": ("Personal Resiliency", "Resiliência Pessoal"),
    "1405": ("Self-Control of Impulses", "Autocontrole dos Impulsos"),
    "1407": ("Substance Addiction Consequences", "Consequências da Dependência de Substâncias"),
    "1500": ("Parent-Infant Attachment", "Vínculo Pais-Lactente"),
    "1501": ("Role Performance", "Desempenho de Papel"),
    "1502": ("Social Interaction Skills", "Habilidades de Interação Social"),
    "1503": ("Social Involvement", "Envolvimento Social"),
    "1504": ("Social Support", "Apoio Social"),
    "1600": ("Adherence Behavior", "Comportamento de Adesão"),
    "1602": ("Health Promoting Behavior", "Comportamento de Promoção da Saúde"),
    "1604": ("Leisure Participation", "Participação em Atividades de Lazer"),
    "1605": ("Pain Control", "Controle da Dor"),
    "1613": ("Self-Management of Care", "Autogestão dos Cuidados"),
    "1618": ("Nausea & Vomiting Control", "Controle de Náuseas e Vômitos"),
    "1619": ("Self-Management: Diabetes", "Autogestão do Diabetes"),
    "1626": ("Weight Gain Behavior", "Comportamento de Ganho de Peso"),
    "1627": ("Weight Loss Behavior", "Comportamento de Perda de Peso"),
    "1628": ("Weight Maintenance Behavior", "Comportamento de Manutenção do Peso"),
    "1633": ("Exercise Participation", "Participação em Exercício"),
    "1701": ("Health Beliefs: Perceived Ability to Perform", "Crenças de Saúde: Capacidade Percebida para Agir"),
    "1803": ("Knowledge: Disease Management", "Conhecimento: Controle da Doença"),
    "1902": ("Risk Control", "Controle de Risco"),
    "1914": ("Risk Control: Cardiovascular Disease", "Controle do Risco: Doença Cardiovascular"),
    "1908": ("Risk Detection", "Detecção de Risco"),
    "1909": ("Fall Prevention Behaviour", "Comportamento de Prevenção de Quedas"),
    "1919": ("Elopement", "Fuga"),
    "1920": ("Elopement Risk", "Risco de Fuga"),
    "1924": ("Risk Control: Infectious Process", "Controle de Risco: Processo Infeccioso"),
    "1927": ("Risk Control: Dry Eye", "Controle de Risco: Olho Seco"),
    "1928": ("Risk Control: Hypertension", "Controle do Risco: Hipertensão"),
    "1933": ("Risk Control: Hypotension", "Controle do Risco: Hipotensão"),
    "1947": ("Safe Home Environment: Child's Room", "Ambiente Domiciliar Seguro: Quarto da Criança"),
    "1932": ("Risk Control: Thrombus", "Controle do Risco: Trombo"),
    "2001": ("Spiritual Health", "Saúde Espiritual"),
    "2002": ("Personal Well-Being", "Bem-Estar Pessoal"),
    "2010": ("Comfort Status: Physical", "Estado de Conforto: Físico"),
    "2011": ("Comfort Status: Psychospiritual", "Estado de Conforto: Psicoespiritual"),
    "2012": ("Comfort Status: Sociocultural", "Estado de Conforto: Sociocultural"),
    "2015": ("Health Literacy Behavior", "Comportamento de Literacia em Saúde"),
    "2102": ("Pain Level", "Nível de Dor"),
    "2108": ("Substance Withdrawal Severity", "Severidade da Abstinência de Substâncias"),
    "2109": ("Discomfort Level", "Nível de Desconforto"),
    "2110": ("Dry Eye Severity", "Gravidade do Olho Seco"),
    "2117": ("Lymphedema Severity", "Gravidade do Linfedema"),
    "2203": ("Caregiver Lifestyle Disruption", "Perturbação do Estilo de Vida do Cuidador"),
    "2208": ("Caregiver Stressors", "Estressores do Cuidador"),
    "2210": ("Caregiver Role Endurance", "Resistência no Papel de Cuidador"),
    "2211": ("Parenting Performance", "Desempenho da Parentalidade"),
    "2303": ("Post-Procedure Recovery", "Recuperação Pós-Procedimento"),
    "2304": ("Surgical Recovery: Convalescence", "Recuperação Cirúrgica: Convalescença"),
    "2501": ("Protection from Abuse", "Proteção contra Abuso"),
    "2508": ("Caregiver Well-Being", "Bem-Estar do Cuidador"),
    "2509": ("Maternal Status: Antepartum", "Estado Materno: Anteparto"),
    "2510": ("Maternal Status: Intrapartum", "Estado Materno: Durante o Parto"),
    "2511": ("Maternal Status: Postpartum", "Estado Materno: Puerpério"),
    "2600": ("Family Coping", "Enfrentamento Familiar"),
    "2602": ("Family Functioning", "Funcionamento Familiar"),
    "2603": ("Family Integrity", "Integridade Familiar"),
    "2606": ("Family Health Status", "Estado de Saúde Familiar"),
    "2700": ("Social Competence", "Competência Social"),
    "2701": ("Community Health Status", "Estado de Saúde da Comunidade"),
    "2704": ("Community Resilience", "Resiliência da Comunidade"),
    "3207": ("Knowledge: Lymphedema Management", "Conhecimento: Controle do Linfedema"),
}



EN_GB_REPLACEMENTS = {
    "Behavioral": "Behavioural",
    "behavioral": "behavioural",
    "Behavior": "Behaviour",
    "behavior": "behaviour",
    "Counseling": "Counselling",
    "counseling": "counselling",
    "Organization": "Organisation",
    "organization": "organisation",
    "Organizational": "Organisational",
    "organizational": "organisational",
    "Aging": "Ageing",
    "aging": "ageing",
    "Labor": "Labour",
    "labor": "labour",
    "Anemia": "Anaemia",
    "anemia": "anaemia",
    "Hemoglobin": "Haemoglobin",
    "hemoglobin": "haemoglobin",
    "Hemodynamic": "Haemodynamic",
    "hemodynamic": "haemodynamic",
    "Hemorrhage": "Haemorrhage",
    "hemorrhage": "haemorrhage",
    "Hemorrhagic": "Haemorrhagic",
    "hemorrhagic": "haemorrhagic",
    "Edema": "Oedema",
    "edema": "oedema",
    "Pediatric": "Paediatric",
    "pediatric": "paediatric",
    "Anesthesia": "Anaesthesia",
    "anesthesia": "anaesthesia",
    "Postanesthesia": "Post-anaesthesia",
    "postanesthesia": "post-anaesthesia",
    "Diarrhea": "Diarrhoea",
    "diarrhea": "diarrhoea",
    "Esophagus": "Oesophagus",
    "esophagus": "oesophagus",
    "Gynecologic": "Gynaecologic",
    "gynecologic": "gynaecologic",
    "Tumor": "Tumour",
    "tumor": "tumour",
    "Center": "Centre",
    "center": "centre",
}


def to_en_gb(text: str) -> str:
    """Localise user-facing English classification text to en-GB spelling.

    Classification codes and edition references remain the canonical identifiers.
    """
    out = text
    # Longest keys first prevents partial replacements such as Behavior before Behavioral.
    for source in sorted(EN_GB_REPLACEMENTS, key=len, reverse=True):
        out = out.replace(source, EN_GB_REPLACEMENTS[source])
    return out

BASELINE_REF = "https://nursing.uiowa.edu/center-for-nursing-classification-and-clinical-effectiveness"
NIC8_LIST_REF = "https://www.salusplay.com/blog/clasificacion-completa-intervenciones-enfermeria-nic-2024/"
NOC7_LIST_REF = "https://www.salusplay.com/apuntes/pae-y-diagnosticos-de-enfermeria-nanda-noc-y-nic/anexo-2-clasificacion-completa-de-resultados-de-enfermeria-noc-2024-8"
NANDA_REF = "https://nanda.org/nanda-book/"
REFS = {
    "leisure": "https://doi.org/10.1111/j.2047-3095.2013.01233.x",
    "loneliness": "https://doi.org/10.1177/20473087261445590",
    "health_literacy": "https://doi.org/10.1111/2047-3095.12482",
    "self_family": "https://doi.org/10.1111/jan.15503",
    "family": "https://doi.org/10.1111/2047-3095.12323",
    "dry_eye": "https://doi.org/10.1097/01.NPR.0000920536.53179.f8",
    "lymphedema": "https://doi.org/10.11606/T.7.2024.tde-05062025-140418",
    "urinary": "https://doi.org/10.1111/2047-3095.12080",
    "respiratory": "https://doi.org/10.1111/2047-3095.12307",
    "perfusion": "https://doi.org/10.1590/0034-7167-2017-0504",
    "delirium": "https://doi.org/10.3390/ijerph16224504",
    "energy_field": "https://doi.org/10.1590/0034-7167-2025-0119",
    "breastfeeding": "https://doi.org/10.1111/2047-3095.12256",
    "hyperbili": "https://uvadoc.uva.es/handle/10324/76379",
    "frailty": "https://doi.org/10.1111/2047-3095.12225",
    "social": "https://doi.org/10.1111/jan.16652",
}


def make(nic: str, noc: str, confidence: str = "moderate", ref: str = BASELINE_REF, rationale: str = "Direct semantic alignment with the diagnosis focus using current-edition NIC/NOC concepts."):
    if nic not in NIC:
        raise KeyError(f"NIC {nic} missing from catalog")
    if noc not in NOC:
        raise KeyError(f"NOC {noc} missing from catalog")
    return {
        "nic_code": nic,
        "nic_label_en": to_en_gb(NIC[nic][0]),
        "nic_label_pt": NIC[nic][1],
        "noc_code": noc,
        "noc_label_en": to_en_gb(NOC[noc][0]),
        "noc_label_pt": NOC[noc][1],
        "mapping_confidence": confidence,
        "mapping_reference": ref,
        "mapping_rationale": rationale,
    }


def mapping_for(code: str, desc: str, domain: str, clazz: str):
    d = desc.lower()

    # Domain 1: health promotion / self-management
    if code in {"00097", "00448"}: return make("5360", "1604", "high", REFS["leisure"], "Leisure/recreation intervention and outcome directly target reduced diversional engagement.")
    if code in {"00355", "00394", "00307"}: return make("0200", "1633", "high", REFS["self_family"], "Exercise participation directly measures the target behavior; Exercise Promotion is the primary behavioral intervention.")
    if code == "00273": return make("5465", "2002", "moderate", REFS["energy_field"], "Current literature specifically discusses the diagnostic concept in relation to Therapeutic Touch; well-being is used as a conservative measurable patient outcome.")
    if code in {"00276", "00369"}: return make("4480", "1613", "moderate", REFS["self_family"], "Self-direction and responsibility are closer to self-management than generic disease knowledge alone.")
    if code == "00293": return make("5510", "1602", "moderate", REFS["self_family"], "Readiness for improved self-management is best tracked as health-promoting behavior with education support.")
    if code in {"00080", "00410"}: return make("7110", "2606", "high", REFS["family"], "Family involvement and Family Health Status are contemporary family-management linkages.")
    if code in {"00356", "00413"}: return make("8500", "2701", "high", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8250918/", "Community-level management requires a community intervention and community health outcome rather than individual education alone.")
    if code == "00489": return make("5602", "1619", "high", REFS["self_family"], "Diabetes self-management is the direct NOC construct for blood-glucose self-management risk.")
    if code == "00277": return make("1350", "2110", "high", REFS["dry_eye"], "Dry Eye Prevention and Dry Eye Severity directly address the diagnosis focus.")
    if code in {"00352", "00412"}: return make("1710", "1100", "moderate", BASELINE_REF, "Oral-health maintenance and Oral Health are closer to dry-mouth consequences than generic disease knowledge.")
    if code == "00397": return make("0180", "0007", "high", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8242432/", "Energy Management and Fatigue Level directly address fatigue self-management.")
    if code in {"00278", "00281"}: return make("5602", "2117", "high", REFS["lymphedema"], "Lymphedema Severity is a current NOC outcome; disease-process teaching supports self-management education.")
    if code == "00384": return make("1450", "1618", "high", REFS["self_family"], "Nausea Management and Nausea & Vomiting Control directly match the diagnosis focus.")
    if code == "00418": return make("1400", "1605", "high", REFS["self_family"], "Pain Management with Pain Control measures self-management success better than symptom level alone.")
    if code == "00447": return make("1260", "1628", "high", REFS["self_family"], "Weight Management with Weight Maintenance Behavior matches readiness for weight self-management.")
    if code in {"00398", "00487"}: return make("1280", "1627", "high", REFS["self_family"], "Weight-reduction assistance and Weight Loss Behavior directly target overweight self-management.")
    if code in {"00485", "00486"}: return make("1240", "1626", "high", REFS["self_family"], "Weight-gain assistance and Weight Gain Behavior directly target underweight self-management.")
    if code in {"00292", "00395"}: return make("4480", "1602", "moderate", REFS["self_family"], "Health-maintenance behavior is better represented by health-promoting behavior than disease-process knowledge.")
    if code in {"00300", "00308", "00309"}: return make("7180", "0306", "high", REFS["family"], "Home Maintenance Assistance and instrumental ADL performance directly cover maintaining a safe functional home.")
    if code in {"00339", "00411", "00262"}: return make("5515", "2015", "high", REFS["health_literacy"], "Current literature explicitly pairs Health Literacy Enhancement (5515) with Health Literacy Behavior (2015).")
    if code == "00340": return make("8340", "0113", "moderate", REFS["frailty"], "Resilience promotion plus Physical Aging provides a measurable healthy-aging trajectory.")
    if code in {"00353", "00357"}: return make("0180", "0300", "high", REFS["frailty"], "Frailty linkage evidence emphasizes energy, mobility and self-care; ADL performance is an appropriate primary outcome.")

    # Domain 2: nutrition
    if code in {"00343", "00409", "00419", "00359", "00360", "00270", "00269"}: return make("1100", "1004", "high", BASELINE_REF, "Nutrition Management and Nutritional Status directly address intake/eating dynamics.")
    if code in {"00371", "00406", "00347", "00382", "00479"}: return make("5244", "1000", "high", NIC8_LIST_REF, "NIC 8th no longer lists legacy 1054; Breastfeeding Counselling (5244) is current and directly supports breastfeeding establishment.")
    if code in {"00333", "00334"}: return make("5244", "1001", "high", NIC8_LIST_REF, "Breastfeeding Counselling (5244) is the current NIC 8th counselling intervention; maternal breastfeeding establishment directly measures the maternal side of milk production/feeding establishment.")
    if code == "00271": return make("1050", "1008", "moderate", BASELINE_REF, "Feeding support and Food/Fluid Intake directly address ineffective infant feeding dynamics.")
    if code == "00103": return make("1860", "1010", "high", "https://doi.org/10.1177/20473087261443252", "Swallowing Therapy and Swallowing Status directly address impaired swallowing.")
    if code in {"00194", "00230"}: return make("6924", "0118", "high", REFS["hyperbili"], "Phototherapy: Neonate is current NIC; Newborn Adaptation provides a broader measurable neonatal outcome including bilirubin-related transition.")
    if code == "00491": return make("2080", "0606", "high", REFS["self_family"], "Fluid/Electrolyte Management and Electrolyte Balance directly address the risk.")
    if code == "00492": return make("4120", "0601", "high", BASELINE_REF, "Fluid Management and Fluid Balance directly address fluid-volume balance.")
    if code in {"00026", "00370"}: return make("4120", "0603", "high", BASELINE_REF, "Fluid Overload Severity directly measures excessive fluid volume.")
    if code in {"00421", "00420"}: return make("4120", "0602", "high", BASELINE_REF, "Hydration directly measures inadequate fluid volume while Fluid Management targets correction/prevention.")

    # Domain 3: elimination / exchange
    if code == "00016": return make("0590", "0503", "high", REFS["urinary"], "Urinary Elimination Management and Urinary Elimination directly match the diagnosis.")
    if code == "00322": return make("0620", "0503", "high", REFS["urinary"], "Corrects the prior code error: 0620 is Urinary Retention Care; 0610 is incontinence care.")
    if code in {"00297", "00310", "00017", "00019", "00022"}: return make("0610", "0502", "high", REFS["urinary"], "Urinary Incontinence Care and Urinary Continence directly address incontinence.")
    if code in {"00423", "00422"}: return make("0430", "1015", "high", NOC7_LIST_REF, "Corrects obsolete/invalid NOC code 1050: Gastrointestinal Function is 1015 in NOC 7th edition; Bowel Management supports motility management.")
    if code in {"00344", "00346"}: return make("0430", "0501", "high", BASELINE_REF, "Bowel Management and Bowel Elimination directly address intestinal elimination.")
    if code in {"00235", "00236"}: return make("0450", "0501", "high", BASELINE_REF, "Constipation/Impaction Management is diagnosis-specific; Bowel Elimination measures resolution.")
    if code in {"00424", "00345"}: return make("0410", "0500", "high", BASELINE_REF, "Bowel Incontinence Care and Bowel Continence directly address fecal continence.")
    if code == "00030": return make("3350", "0402", "high", REFS["respiratory"], "Respiratory Monitoring and Respiratory Status: Gas Exchange are established linkages for impaired gas exchange.")

    # Domain 4: activity/rest
    if domain == "4" and clazz == "1": return make("1850", "0004", "high", BASELINE_REF, "Sleep Enhancement and Sleep directly match sleep-pattern and sleep-hygiene diagnoses.")
    if code in {"00085", "00324", "00091", "00363", "00364"}: return make("0221", "0208", "moderate", BASELINE_REF, "Ambulation-focused exercise therapy supports mobility; Mobility is the direct broad outcome.")
    if code == "00089": return make("0846", "0208", "high", BASELINE_REF, "Wheelchair positioning is specific to impaired wheelchair mobility; Mobility measures functional change.")
    if code == "00367": return make("0970", "0208", "high", BASELINE_REF, "Transfer intervention directly matches impaired transferring ability.")
    if code == "00365": return make("0221", "0200", "high", BASELINE_REF, "Exercise Therapy: Ambulation and Ambulation directly target walking ability.")
    if code in {"00298", "00299"}: return make("0180", "0005", "high", REFS["respiratory"], "Energy Management and Activity Tolerance are established linkages for reduced activity tolerance.")
    if code == "00477": return make("0180", "0007", "high", REFS["respiratory"], "Energy Management and Fatigue Level directly target excessive fatigue burden.")
    if code in {"00465", "00464"}: return make("2870", "2304", "high", "https://doi.org/10.1016/j.enfcli.2023.02.003", "Postanesthesia/perioperative care with Surgical Recovery: Convalescence directly addresses delayed recovery.")
    if code == "00311": return make("4050", "1914", "high", NOC7_LIST_REF, "Cardiac Risk Management and Risk Control: Cardiovascular Disease directly target cardiovascular risk; Cardiopulmonary Function remains a contextual physiologic outcome.")
    if code == "00362": return make("4150", "0401", "moderate", BASELINE_REF, "Hemodynamic regulation and Circulation Status are aligned to blood-pressure instability risk.")
    if code == "00240": return make("4040", "0400", "high", BASELINE_REF, "Cardiac Care and Cardiac Pump Effectiveness directly address cardiac-output risk.")
    if code == "00201": return make("2620", "0406", "high", "https://doi.org/10.3390/ijerph16224504", "Neurologic Monitoring and Tissue Perfusion: Cerebral directly address cerebral perfusion risk.")
    if code in {"00204", "00228"}: return make("4062", "0407", "high", REFS["perfusion"], "Circulatory Care: Arterial Insufficiency and Tissue Perfusion: Peripheral are validated direct concepts.")
    if code in {"00032", "00033", "00431", "00430"}: return make("3390", "0403", "high", REFS["respiratory"], "Ventilation Assistance and Respiratory Status: Ventilation directly address ineffective ventilation/breathing.")
    if code in {"00331", "00332", "00442"}: return make("1800", "0300", "high", BASELINE_REF, "General self-care assistance and ADL self-care behavior match the syndrome/readiness construct.")
    if code == "00326": return make("1801", "0301", "high", "https://doi.org/10.1177/20473087261443252", "Bathing/Hygiene self-care assistance and bathing outcome directly match decreased bathing ability.")
    if code == "00327": return make("1802", "0302", "high", BASELINE_REF, "Dressing/Grooming assistance and dressing outcome directly match decreased dressing ability.")
    if code == "00328": return make("1803", "0303", "high", BASELINE_REF, "Feeding self-care assistance and eating outcome directly match decreased feeding ability.")
    if code == "00330": return make("1802", "0305", "high", BASELINE_REF, "Dressing/Grooming assistance includes grooming support; Hygiene measures functional grooming/hygiene performance.")
    if code == "00329": return make("1804", "0310", "high", REFS["urinary"], "Toileting self-care assistance and toileting outcome directly match decreased toileting ability.")
    if code in {"00375", "00414"}: return make("1720", "0308", "high", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8516802/", "Oral Health Promotion and Oral Hygiene self-care directly match ineffective oral hygiene behavior.")

    # Domain 5: perception/cognition
    if code == "00128": return make("6440", "0900", "high", REFS["delirium"], "Delirium Management and Cognition are validated for acute confusion.")
    if code == "00173": return make("4820", "0901", "high", REFS["delirium"], "Reality Orientation and Cognitive Orientation are established for acute-confusion risk.")
    if code == "00129": return make("6460", "0900", "high", BASELINE_REF, "Dementia Management is specific to chronic confusional states; Cognition measures status.")
    if code == "00222": return make("4370", "1405", "high", NOC7_LIST_REF, "Impulse Control Training and Self-Control of Impulses directly align with ineffective impulse control in the current editions.")
    if code == "00493": return make("4720", "0900", "moderate", BASELINE_REF, "Cognitive Stimulation and Cognition align with disrupted thought processes.")
    if code in {"00435", "00499"}: return make("5602", "1803", "high", BASELINE_REF, "Teaching: Disease Process and Knowledge: Disease Management directly address inadequate/enhanced health knowledge.")
    if code == "00131": return make("4760", "0908", "high", BASELINE_REF, "Memory Training and Memory directly target impaired memory.")
    if code in {"00429", "00184", "00242", "00244", "00243"}: return make("5250", "0906", "high", "https://doi.org/10.1111/2047-3095.12392", "Decision-Making Support and Decision-Making directly address decision capacity/readiness.")
    if code in {"00051", "00434", "00368"}: return make("4976", "0902", "high", REFS["delirium"], "Communication Enhancement: Speech Deficit and Communication are a direct verbal-communication pairing.")

    # Domain 6: self-perception
    if code in {"00167", "00494"}: return make("5390", "1205", "moderate", BASELINE_REF, "Self-awareness work supports self-concept/identity; Self-Esteem provides a measurable self-perception outcome.")
    if code in {"00495", "00496"}: return make("7100", "2603", "high", REFS["family"], "Family Integrity Promotion and Family Integrity directly address family identity disruption.")
    if code == "00488": return make("5270", "2002", "moderate", BASELINE_REF, "Emotional support and personal well-being are conservative targets when dignity is threatened.")
    if code == "00341": return make("5440", "1223" if "1223" in NOC else "1504", "moderate", REFS["loneliness"], "Support-system enhancement supports transgender social identity and social support.")
    if code in {"00483", "00480", "00481", "00482"}: return make("5400", "1205", "high", BASELINE_REF, "Self-Esteem Enhancement and Self-Esteem directly match inadequate self-esteem diagnoses.")
    if code == "00338": return make("5395", "1701", "high", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10099907/", "Self-Efficacy Enhancement and perceived ability to perform directly target health self-efficacy.")
    if code == "00497": return make("5220", "1200", "high", BASELINE_REF, "Body Image Enhancement and Body Image directly match the diagnosis.")

    # Domain 7: roles/relationships
    if code in {"00436", "00437", "00438", "00387"}: return make("8300", "2211", "high", REFS["family"], "Parenting Promotion and Parenting Performance directly address parenting behavior/role conflict.")
    if code in {"00389", "00440", "00388", "00159"}: return make("7100", "2602", "high", REFS["family"], "Family Integrity/Process interventions and Family Functioning directly address family interaction/process patterns.")
    if code == "00439": return make("7110", "1500", "moderate", REFS["family"], "Family involvement supports attachment processes; Parent-Infant Attachment is the closest NOC outcome.")
    if code == "00055": return make("5370", "1501", "high", REFS["family"], "Role Enhancement and Role Performance directly match ineffective role performance.")
    if code in {"00449", "00445", "00446"}: return make("5240", "1502", "moderate", REFS["social"], "Counseling plus social interaction skills is a safer relationship-focused linkage than the prior pregnancy-specific mapping.")
    if code == "00052": return make("5100", "1502", "high", REFS["social"], "Socialization Enhancement and Social Interaction Skills directly match impaired social interaction.")
    if code in {"00221", "00227", "00208"}: return make("6960", "2509", "moderate", NIC8_LIST_REF, "Legacy NIC 6780 is not present in NIC 8th. Prenatal Care (6960) and Maternal Status: Antepartum (2509) are used as compatibility primaries; intrapartum/postpartum alternatives are exposed separately because childbearing-process care is phase dependent.")

    # Domain 8: sexuality/reproduction
    if code == "00386": return make("5248", "0119", "high", BASELINE_REF, "Sexual Counseling and Sexual Functioning directly address impaired sexual function.")
    if code == "00349": return make("6800", "2509", "high", NIC8_LIST_REF, "Legacy NIC 6780 is not present in NIC 8th. High-Risk Pregnancy Care (6800) with Maternal Status: Antepartum (2509) more directly addresses maternal-fetal dyad risk.")

    # Domain 9: coping/stress tolerance
    if code in {"00141", "00145"}: return make("5230", "1305", "moderate", "https://doi.org/10.1111/2047-3095.12323", "Coping enhancement and psychosocial adjustment are central to post-trauma adaptation.")
    if code == "00484": return make("5350", "1305", "high", REFS["loneliness"], "Relocation Stress Reduction and Psychosocial Adjustment: Life Change directly address migration-transition risk.")
    if code in {"00405", "00158"}: return make("5230", "1302", "high", REFS["family"], "Coping Enhancement and Coping directly address maladaptive/enhanced coping.")
    if code in {"00373", "00075"}: return make("7140", "2600", "high", REFS["family"], "Family Support and Family Coping directly address family coping.")
    if code in {"00456", "00076"}: return make("8500", "2704", "high", NOC7_LIST_REF, "Corrects NOC 2700, which means Social Competence in NOC 7th. Community Resilience (2704) is the more direct community-level coping outcome.")
    if code in {"00366", "00401"}: return make("7040", "2210", "high", REFS["family"], "Caregiver Support and Caregiver Role Endurance directly address caregiving burden/risk.")
    if code in {"00301", "00302", "00285"}: return make("5290", "1304", "high", BASELINE_REF, "Grief Work Facilitation and Grief Resolution directly address grieving.")
    if code in {"00210", "00211", "00212"}: return make("8340", "1309", "high", REFS["family"], "Resilience Promotion and Personal Resiliency directly match resilience diagnoses.")
    if code == "00185": return make("5310", "1201", "high", "https://doi.org/10.1111/2047-3095.12392", "Hope Inspiration and Hope directly match readiness for enhanced hope.")
    if code == "00325": return make("5270", "1205", "moderate", BASELINE_REF, "Emotional support and self-esteem are conservative measurable targets for inadequate self-compassion.")
    if code in {"00400", "00399"}: return make("5820", "1211", "high", BASELINE_REF, "Anxiety Reduction and Anxiety Level directly address excessive anxiety, including death anxiety.")
    if code == "00390": return make("5230", "1210", "high", BASELINE_REF, "Coping support with Fear Level provides a direct measurable fear outcome.")
    if code == "00010": return make("2620", "0910", "high", NOC7_LIST_REF, "Neurologic Monitoring with Neurological Function: Autonomic directly targets autonomic dysreflexia rather than the prior nonspecific Cognition outcome.")
    if code in {"00372", "00241"}: return make("5330", "1204", "high", REFS["loneliness"], "Mood Management and Mood Equilibrium directly target emotion/mood regulation.")
    if code in {"00258", "00259"}: return make("4514", "2108", "high", NOC7_LIST_REF, "Current NIC 8th includes Substance Use Treatment: Drug Withdrawal (4514), and NOC 7th includes Substance Withdrawal Severity (2108); these are more specific to withdrawal than generic addiction consequences.")

    # Domain 10: life principles
    if code == "00175": return make("5480", "2001", "moderate", BASELINE_REF, "Values Clarification supports moral conflict; Spiritual Health is used as a broad value/meaning outcome.")
    if code in {"00454", "00460", "00068"}: return make("5420", "2001", "high", BASELINE_REF, "Spiritual Support and Spiritual Health directly address spiritual well-being.")
    if code in {"00169", "00170", "00171"}: return make("5420", "2001", "moderate", BASELINE_REF, "Spiritual Support and Spiritual Health are the closest broad standardized targets for religiosity diagnoses.")

    # Domain 11: safety/protection
    if code == "00361": return make("6550", "0702", "high", BASELINE_REF, "Infection Protection/immune support and Immune Status directly address impaired immune response.")
    if code in {"00004", "00500"}: return make("6540", "1924", "high", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8242432/", "Infection Control and Risk Control: Infectious Process directly address infection risk.")
    if code in {"00336", "00350", "00351", "00250", "00463", "00469", "00404", "00402"}: return make("6610", "1908", "high", BASELINE_REF, "Risk Identification and Risk Detection are appropriate primary safety linkages.")
    if code == "00245": return make("1650", "1101", "moderate", BASELINE_REF, "Eye Care plus tissue/mucous-membrane integrity targets prevention of corneal injury.")
    if code == "00219": return make("1350", "1927", "high", REFS["dry_eye"], "Dry Eye Prevention and Risk Control: Dry Eye directly address the risk diagnosis.")
    if code == "00087": return make("0842", "0204", "moderate", "https://www.researchgate.net/publication/324549548_Nursing_Outcomes_for_Patients_with_Risk_of_Perioperative_Positioning_Injury", "Intraoperative positioning is diagnosis-specific; NOC 0204 (Immobility Consequences: Physiological) is a current physiologic surveillance outcome but remains broader than positioning injury itself.")
    if code in {"00287", "00313", "00312"}: return make("3520", "1103", "high", BASELINE_REF, "Pressure-injury care and secondary-intention wound healing directly target established pressure injury.")
    if code in {"00288", "00286", "00304"}: return make("3540", "1902", "high", BASELINE_REF, "Pressure Injury Prevention and Risk Control directly target risk states.")
    if code in {"00044", "00046"}: return make("3660", "1101", "high", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8242432/", "Wound/skin care and tissue integrity directly address established tissue/skin impairment.")
    if code in {"00248", "00047"}: return make("3590", "1902", "high", BASELINE_REF, "Skin surveillance and risk control directly address threatened tissue/skin integrity.")
    if code == "00461": return make("5244", "1101", "moderate", NIC8_LIST_REF, "Legacy NIC 1054 is not listed in NIC 8th. Breastfeeding Counselling (5244) can address nipple care/feeding technique while Tissue Integrity tracks the injury; wound/skin interventions may be selected after assessment.")
    if code == "00462": return make("5244", "1902", "moderate", NIC8_LIST_REF, "Legacy NIC 1054 is not listed in NIC 8th. Breastfeeding Counselling (5244) supports preventive technique; general Risk Control remains a compatibility outcome pending patient-specific risk selection.")
    if code in {"00045", "00247"}: return make("1710", "1101", "high", BASELINE_REF, "Oral health maintenance and tissue/mucous-membrane integrity directly address oral mucosa.")
    if code in {"00306", "00303"}: return make("6490", "1909", "high", BASELINE_REF, "Fall Prevention and Fall Prevention Behavior directly address fall risk.")
    if code == "00039": return make("3200", "0410", "high", BASELINE_REF, "Aspiration Precautions and airway patency directly address aspiration risk; corrects the prior overly generic Airway Management mapping.")
    if code == "00031": return make("3250", "0410", "high", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8242432/", "Cough Enhancement and airway patency are established for ineffective airway clearance.")
    if code == "00374": return make("4010", "0413", "high", BASELINE_REF, "Bleeding Precautions and Blood Loss Severity directly address bleeding risk.")
    if code == "00205": return make("4250", "0401", "high", BASELINE_REF, "Shock Management and Circulation Status are direct safety/circulation targets.")
    if code == "00291": return make("6610", "1932", "high", NOC7_LIST_REF, "Risk Identification and Risk Control: Thrombus (1932) directly target thrombosis risk; local VTE protocol remains required.")
    if code == "00425": return make("2660", "0917", "high", "https://doi.org/10.3390/healthcare11172449", "Peripheral sensation monitoring and peripheral neurologic status directly address neurovascular risk.")
    if code == "00156": return make("6824", "1947", "moderate", NOC7_LIST_REF, "Newborn care with a safe child-room environment is more specific than generic Risk Control for SIDS-risk prevention, but it does not replace evidence-based safe-sleep guidance.")
    if code == "00290": return make("6610", "1920", "high", NOC7_LIST_REF, "Risk Identification plus Elopement Risk (1920) is more specific than generic Risk Detection; facility-specific safety procedures remain required.")
    if code == "00138": return make("6487", "1902", "high", BASELINE_REF, "Violence-prevention environmental management and Risk Control directly address other-directed violence risk.")
    if code == "00272": return make("6400", "2501", "high", NOC7_LIST_REF, "Abuse Protection Support plus Protection from Abuse directly align with safeguarding for risk of female genital mutilation; legal and safeguarding protocols remain required.")
    if code in {"00466", "00467", "00468"}: return make("6340", "1902", "high", "https://doi.org/10.1111/2047-3095.12392", "Suicide Prevention and Risk Control are appropriate primary safety mappings for self-injury risk/behavior.")
    if code in {"00181", "00180"}: return make("6540", "1902", "moderate", BASELINE_REF, "Infection/environmental controls with general risk control are used as a conservative contamination linkage.")
    if code == "00217": return make("6410", "0707", "high", BASELINE_REF, "Allergy Management and Immune Hypersensitivity Response directly address allergic-reaction risk.")
    if code == "00042": return make("6570", "0707", "high", BASELINE_REF, "Latex Precautions and Immune Hypersensitivity Response directly address latex-allergy risk.")
    if domain == "11" and clazz == "6": return make("3900", "0800", "high", BASELINE_REF, "Temperature Regulation and Thermoregulation directly match thermoregulation diagnoses.")

    # Domain 12: comfort
    if code in {"00380", "00378"}: return make("6482", "2010", "high", REFS["loneliness"], "Environmental Management: Comfort and physical comfort status directly address physical comfort.")
    if code == "00342": return make("6482", "2109", "moderate", BASELINE_REF, "Comfort-focused environmental care and discomfort level are conservative measurable end-of-life comfort targets.")
    if code in {"00132", "00255", "00133", "00256"}: return make("1400", "2102", "high", BASELINE_REF, "Pain Management and Pain Level directly address pain diagnoses.")
    if code == "00376": return make("5100", "2012", "moderate", REFS["loneliness"], "Socialization enhancement and sociocultural comfort align with readiness for enhanced social comfort.")
    if code == "00383": return make("5100", "1503", "high", REFS["loneliness"], "Socialization Enhancement and Social Involvement directly address inadequate social connectedness.")
    if code == "00358": return make("5440", "1504", "high", REFS["loneliness"], "Support System Enhancement and Social Support directly address inadequate support networks.")
    if code in {"00475", "00335"}: return make("5100", "1203", "high", REFS["loneliness"], "2026 linkage work identifies Loneliness Severity as the resolution outcome and Socialization Enhancement among primary interventions.")
    if code in {"00379", "00377"}: return make("5270", "2011", "high", REFS["loneliness"], "Emotional Support and psychospiritual comfort directly address psychological comfort.")

    # Domain 13: growth/development
    if code in {"00348", "00478"}: return make("1160", "0110", "high", "https://www.scielo.org.mx/scielo.php?pid=S2448-60942024000100206&script=sci_arttext&tlng=en", "Current concept analysis explicitly identifies NOC Growth (0110) and nutritional monitoring/management interventions for delayed child growth.")
    if code in {"00314", "00305"}: return make("8274", "0107", "moderate", NIC8_LIST_REF, "NIC 8274 is now labelled Child Care in NIC 8th. NOC development outcomes are age-specific; 0107 remains only a compatibility representative while age-specific alternatives are returned by the API.")
    if code in {"00315", "00316"}: return make("8278", "0208", "moderate", BASELINE_REF, "Infant developmental enhancement plus Mobility targets infant motor development; age-specific developmental outcomes should supplement this primary mapping.")
    if code in {"00451", "00452", "00453"}: return make("8250", "0117", "high", BASELINE_REF, "Developmental Care is the current NIC label for 8250; Preterm Infant Organization is a direct NOC construct for neurodevelopmental organization.")
    if code == "00295": return make("1050", "1010", "high", BASELINE_REF, "Feeding support plus Swallowing Status targets the suck-swallow response while avoiding the prior inappropriate self-care/eating outcome for an infant.")

    # Safe fallback: use the old structured pair only as a review-required mapping.
    return None


MANIFEST_PATH = (
    ROOT / "data" / "clinical_content_manifest.json"
)

# Fail closed before reviewed clinical prose is consumed.
validate_guidance_content(
    ROOT,
    MANIFEST_PATH,
)

GUIDANCE = json.loads(
    GUIDANCE_PATH.read_text(encoding="utf-8")
)


def local_activity_text(
    description_en: str,
    description_pt: str,
    nic_code: str,
    nic_en: str,
    nic_pt: str,
):
    item = GUIDANCE["nic"].get(nic_code)

    if item is None:
        raise KeyError(
            f"Reviewed NIC guidance missing for {nic_code}"
        )

    if item["label_en"] != nic_en:
        raise ValueError(
            f"NIC {nic_code} EN label drift: "
            f"{item['label_en']!r} != {nic_en!r}"
        )

    if item["label_pt"] != nic_pt:
        raise ValueError(
            f"NIC {nic_code} PT label drift: "
            f"{item['label_pt']!r} != {nic_pt!r}"
        )

    return (
        item["intervention_en"],
        item["intervention_pt"],
    )


def local_outcome_text(
    noc_code: str,
    noc_en: str,
    noc_pt: str,
):
    item = GUIDANCE["noc"].get(noc_code)

    if item is None:
        raise KeyError(
            f"Reviewed NOC guidance missing for {noc_code}"
        )

    if item["label_en"] != noc_en:
        raise ValueError(
            f"NOC {noc_code} EN label drift: "
            f"{item['label_en']!r} != {noc_en!r}"
        )

    if item["label_pt"] != noc_pt:
        raise ValueError(
            f"NOC {noc_code} PT label drift: "
            f"{item['label_pt']!r} != {noc_pt!r}"
        )

    return (
        item["outcome_en"],
        item["outcome_pt"],
    )


def main():
    meta = {item["code"]: item for item in json.loads(META_PATH.read_text(encoding="utf-8"))}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    output = []
    misses = []
    for row in rows:
        code = str(row["code"]).zfill(5)
        info = meta[code]
        description_en = to_en_gb(row["description_en"])

        f03 = GUIDANCE.get("f03", {}).get(code)
        if f03:
            old_description = f03["description_en_from"]
            new_description = f03["description_en_to"]

            if description_en == old_description:
                description_en = new_description
            elif description_en != new_description:
                # F-03 is restricted to the two reviewed lymphoedema
                # records. Accept historical repeated-o corruption only;
                # any other semantic/source drift remains fatal.
                normalized_description = re.sub(
                    r"lympho+edema",
                    "lymphoedema",
                    description_en,
                )

                if normalized_description != new_description:
                    raise ValueError(
                        f"F-03 source drift for {code}: "
                        f"{description_en!r}"
                    )

                description_en = new_description
        mapped = mapping_for(code, description_en, info["domain"], info["class"])
        if mapped is None:
            misses.append((code, description_en, info["domain"], info["class"]))
            continue

        description_pt = info["label_pt"]
        ien, ipt = local_activity_text(
            description_en, description_pt, mapped["nic_code"], mapped["nic_label_en"], mapped["nic_label_pt"]
        )
        oen, opt = local_outcome_text(mapped["noc_code"], mapped["noc_label_en"], mapped["noc_label_pt"])
        row.update(
            code=code,
            description_en=description_en,
            description_pt=description_pt,
            intervention_en=ien,
            intervention_pt=ipt,
            outcome_en=oen,
            outcome_pt=opt,
            nanda_edition=NANDA_EDITION,
            nanda_domain=info["domain"],
            nanda_class=info["class"],
            nanda_source_page=str(info["source_page"]),
            nanda_pdf_page=str(info["pdf_page"]),
            nic_edition=NIC_EDITION,
            nic_code=mapped["nic_code"],
            nic_label_en=mapped["nic_label_en"],
            nic_label_pt=mapped["nic_label_pt"],
            noc_edition=NOC_EDITION,
            noc_code=mapped["noc_code"],
            noc_label_en=mapped["noc_label_en"],
            noc_label_pt=mapped["noc_label_pt"],
            mapping_status="curated_current_editions_contextual",
            mapping_confidence=mapped["mapping_confidence"],
            mapping_methodology="Context-aware educational NANDA-to-NIC/NOC mapping curated against NANDA-I 2024-2026 (13th), NIC 8th, and NOC 7th. Legacy primary fields are retained for compatibility; the API also exposes alternative/context-specific links. It is not an official crosswalk and does not replace clinical judgment or local protocols.",
            mapping_review_date=REVIEW_DATE,
            mapping_reference=mapped["mapping_reference"],
            mapping_rationale=to_en_gb(mapped["mapping_rationale"]),
            mapping_notes="Compatibility primary mapping plus context-specific alternatives where indicated. Select interventions/outcomes after patient assessment; use licensed source content for definitions, indicators, activities, scales, and scoring.",
        )
        output.append(row)

    if misses:
        print("UNMAPPED", len(misses))
        for item in misses:
            print(item)
        raise SystemExit(2)

    fields = [
        "code", "description_en", "description_pt",
        "intervention_en", "intervention_pt", "outcome_en", "outcome_pt",
        "nanda_edition", "nanda_domain", "nanda_class", "nanda_source_page", "nanda_pdf_page",
        "nic_edition", "nic_code", "nic_label_en", "nic_label_pt",
        "noc_edition", "noc_code", "noc_label_en", "noc_label_pt",
        "mapping_status", "mapping_confidence", "mapping_methodology", "mapping_review_date",
        "mapping_reference", "mapping_rationale", "mapping_notes",
    ]
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    from collections import Counter
    confidence = Counter(r["mapping_confidence"] for r in output)
    nic = Counter(r["nic_code"] for r in output)
    noc = Counter(r["noc_code"] for r in output)
    print(f"Rebuilt {len(output)} mappings. Confidence={dict(confidence)}; unique NIC={len(nic)}; unique NOC={len(noc)}")
    print("Top NIC", nic.most_common(10))
    print("Top NOC", noc.most_common(10))


if __name__ == "__main__":
    main()
