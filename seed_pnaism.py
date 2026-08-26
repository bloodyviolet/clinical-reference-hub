import database

# Ensure tables exist
database.Base.metadata.create_all(bind=database.engine)

# Official PNAISM Directives extracted directly from the PNPM Errata
pnaism_directives = [
    {
        "directive": "Atenção Clínico-Ginecológica",
        "target_demographic": "População Feminina Geral",
        "clinical_guideline": "Prevenção e tratamento de doenças cardiovasculares, hipertensão arterial e diabetes mellitus, com critérios de priorização para consultas e exames."
    },
    {
        "directive": "Planejamento Reprodutivo",
        "target_demographic": "Mulheres e Homens, Adultos e Adolescentes",
        "clinical_guideline": "Garantia de acesso à anticoncepção reversível e cirúrgica, contracepção de emergência nas unidades básicas, e assistência em infertilidade."
    },
    {
        "directive": "Atenção Obstétrica e Neonatal (Rede Cegonha / RAMI)",
        "target_demographic": "Gestantes e Puérperas",
        "clinical_guideline": "Garantia de 6 ou mais consultas de pré-natal com classificação de risco, atenção humanizada ao parto com acompanhante e doula, e redução da morbimortalidade materna."
    },
    {
        "directive": "Atenção ao Abortamento e Aborto Legal",
        "target_demographic": "Mulheres em Situação de Abortamento",
        "clinical_guideline": "Atenção qualificada ao abortamento incompleto (AMIU/curetagem) com tratamento para dor, e garantia de aborto legal sem exigência de Boletim de Ocorrência."
    },
    {
        "directive": "Atenção às Vítimas de Violência Doméstica e Sexual",
        "target_demographic": "Mulheres e Adolescentes em Situação de Violência",
        "clinical_guideline": "Organização de rede integrada com oferta de contracepção de emergência, profilaxia de DST/HIV, e notificação compulsória no SINAN-VIVA."
    },
    {
        "directive": "Prevenção e Controle de DST/HIV/Aids",
        "target_demographic": "Mulheres Vivendo com HIV/Aids",
        "clinical_guideline": "Redução da transmissão vertical do HIV e Sífilis congênita, com garantia de acesso à Terapia Antirretroviral (TARV) para gestantes."
    },
    {
        "directive": "Prevenção do Câncer de Mama e Colo do Útero",
        "target_demographic": "Mulheres de 25 a 69 anos",
        "clinical_guideline": "Garantia de mamografia (50 a 69 anos) e citopatológico (25 a 59 anos), com acesso à cirurgia de reconstrução mamária e acompanhamento oncológico."
    },
    {
        "directive": "Atenção à Saúde Mental com Enfoque de Gênero",
        "target_demographic": "Mulheres com Sofrimento Psíquico",
        "clinical_guideline": "Atenção qualificada à depressão (pós-parto e climatério), prevenção do suicídio, e assistência a usuárias de álcool e drogas (CAPSad)."
    },
    {
        "directive": "Atenção à Saúde da Mulher no Climatério",
        "target_demographic": "Mulheres no Climatério",
        "clinical_guideline": "Disponibilização de terapia de reposição hormonal, terapias complementares e grupos de informação nas unidades de saúde."
    },
    {
        "directive": "Atenção à Saúde das Mulheres Idosas",
        "target_demographic": "Mulheres Idosas",
        "clinical_guideline": "Ações de promoção da saúde, prevenção de fraturas de fêmur, avaliação de capacidade funcional e apoio a mulheres cuidadoras."
    },
    {
        "directive": "Atenção à Saúde das Mulheres Negras",
        "target_demographic": "Mulheres Negras e Quilombolas",
        "clinical_guideline": "Implementação do Programa de Anemia Falciforme com exames de eletroforese de hemoglobina e combate ao racismo institucional no atendimento."
    },
    {
        "directive": "Atenção à Saúde das Mulheres Lésbicas e Bissexuais",
        "target_demographic": "Mulheres Lésbicas e Bissexuais",
        "clinical_guideline": "Garantia de acesso à prevenção de câncer ginecológico e DSTs, coibindo a postergação de atendimento motivada por preconceito de orientação sexual."
    },
    {
        "directive": "Atenção à Saúde das Trabalhadoras Rurais e Assentadas",
        "target_demographic": "Mulheres Trabalhadoras do Campo, Águas e Floresta",
        "clinical_guideline": "Atenção aos agravos de saúde relacionados ao trabalho rural e notificação de Acidentes de Trabalho (CAT)."
    },
    {
        "directive": "Atenção à Saúde das Mulheres Indígenas",
        "target_demographic": "Mulheres Indígenas",
        "clinical_guideline": "Ações de saúde nos polos básicos articuladas com os Distritos Sanitários Especiais Indígenas (DSEI), respeitando as demandas socioculturais do grupo."
    },
    {
        "directive": "Atenção à Saúde das Mulheres Privadas de Liberdade",
        "target_demographic": "Mulheres em Situação de Prisão",
        "clinical_guideline": "Proibição do uso de algemas durante parto e abortamento, garantia de áreas especiais para gestantes e lactantes, e acesso a medicamentos essenciais."
    },
    {
        "directive": "Atenção à Saúde das Mulheres com Deficiência",
        "target_demographic": "Mulheres com Deficiência",
        "clinical_guideline": "Ações voltadas aos agravos específicos do grupo e garantia de acessibilidade nos serviços de saúde reprodutiva e clínica."
    }
]

def seed_pnaism():
    db = database.SessionLocal()
    
    try:
        # Clear existing entries to prevent duplicates
        db.query(database.PNAISMPolicy).delete()
        db.commit()

        print("Seeding PNAISM database from official PNPM guidelines...")
        count = 0
        
        for item in pnaism_directives:
            entry = database.PNAISMPolicy(
                directive=item["directive"],
                target_demographic=item["target_demographic"],
                clinical_guideline=item["clinical_guideline"]
            )
            db.add(entry)
            count += 1
            
        db.commit()
        print(f"Successfully seeded {count} PNAISM clinical directives into SQLite.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_pnaism()
