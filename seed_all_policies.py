import database
from sqlalchemy import Column, Integer, String, Text

# Ensure tables exist (Assuming you add these models to your database.py)
# If they aren't in your database.py yet, this script defines them dynamically for SQLite.
database.Base.metadata.create_all(bind=database.engine)

# --- 1. PNAISH (Saúde do Homem) ---
pnaish_directives = [
    {
        "directive": "Atenção Clínico-Ginecológica/Urológica",
        "target_demographic": "Homens de 20 a 59 anos",
        "clinical_guideline": "Prevenção e tratamento de câncer de próstata e pênis, além do controle da hipertrofia prostática benigna e disfunções sexuais (erétil)."
    },
    {
        "directive": "Doenças Cardiovasculares e Crônicas",
        "target_demographic": "População Masculina Adulta",
        "clinical_guideline": "Captação precoce para prevenção primária e tratamento de hipertensão arterial, doenças isquêmicas do coração e diabetes mellitus."
    },
    {
        "directive": "Prevenção de Violência e Causas Externas",
        "target_demographic": "Homens Jovens (20 a 39 anos)",
        "clinical_guideline": "Ações de prevenção de acidentes de transporte terrestre, agressões e lesões autoprovocadas (suicídio), que representam a maior causa de mortalidade nesta faixa."
    },
    {
        "directive": "Controle do Tabagismo e Alcoolismo",
        "target_demographic": "População Masculina Geral",
        "clinical_guideline": "Ações de prevenção e tratamento para o uso abusivo de álcool e tabaco, fortemente associados à morbimortalidade masculina (cirrose, acidentes, câncer)."
    },
    {
        "directive": "Paternidade e Planejamento Reprodutivo",
        "target_demographic": "Homens (Adolescentes e Adultos)",
        "clinical_guideline": "Inclusão do homem nas ações de planejamento familiar, incentivo à paternidade responsável e garantia de oferta da vasectomia voluntária."
    },
    {
        "directive": "Prevenção de DST/HIV/Aids",
        "target_demographic": "Homens com Vida Sexual Ativa",
        "clinical_guideline": "Promoção do uso de preservativo como dupla proteção (gravidez e DSTs) e facilitação do acesso a testes rápidos e tratamento."
    }
]

# --- 2. PNAISC (Saúde da Criança) ---
pnaisc_directives = [
    {
        "directive": "Atenção Humanizada à Gestação e Nascimento",
        "target_demographic": "Gestantes e Recém-Nascidos",
        "clinical_guideline": "Promoção do contato pele a pele imediato, clampeamento tardio do cordão, Método Canguru para baixo peso e '5º Dia de Saúde Integral' na Atenção Básica."
    },
    {
        "directive": "Aleitamento Materno e Alimentação Complementar",
        "target_demographic": "Crianças de 0 a 2 anos",
        "clinical_guideline": "Promoção do aleitamento materno exclusivo até os 6 meses e complementado até os 2 anos, apoiado pela Rede de Bancos de Leite Humano."
    },
    {
        "directive": "Acompanhamento do Crescimento e Desenvolvimento",
        "target_demographic": "Primeira Infância (0 a 5 anos)",
        "clinical_guideline": "Vigilância do desenvolvimento neuropsicomotor e crescimento utilizando a Caderneta de Saúde da Criança, com foco em famílias vulneráveis."
    },
    {
        "directive": "Atenção a Doenças Prevalentes (AIDPI)",
        "target_demographic": "Crianças menores de 5 anos",
        "clinical_guideline": "Manejo qualificado de doenças respiratórias, diarreicas e desnutrição, além da suplementação de Vitamina A e Ferro."
    },
    {
        "directive": "Prevenção de Violências e Acidentes",
        "target_demographic": "Crianças de 0 a 9 anos",
        "clinical_guideline": "Notificação compulsória de violências (Sinan-Viva) e ações de promoção da cultura de paz e prevenção de acidentes domésticos e de trânsito."
    },
    {
        "directive": "Triagens Neonatais Universais",
        "target_demographic": "Recém-nascidos",
        "clinical_guideline": "Garantia da realização do Teste do Pezinho (biológico), Orelhinha (auditivo), Olhinho (ocular) e Coraçãozinho (oximetria) antes da alta ou na primeira semana."
    }
]

# --- 3. PNAB (Atenção Básica) ---
pnab_directives = [
    {
        "directive": "Acolhimento e Demanda Espontânea",
        "target_demographic": "População em Geral",
        "clinical_guideline": "Recepção de todos os usuários com escuta qualificada, classificação de risco e avaliação de vulnerabilidade, sem restrição de acesso."
    },
    {
        "directive": "Longitudinalidade e Coordenação do Cuidado",
        "target_demographic": "Famílias Adscritas",
        "clinical_guideline": "Acompanhamento contínuo dos usuários, gerenciamento de projetos terapêuticos e coordenação do fluxo na Rede de Atenção à Saúde (RAS)."
    },
    {
        "directive": "Atenção Domiciliar",
        "target_demographic": "Pacientes com Dificuldade de Locomoção",
        "clinical_guideline": "Realização de visitas domiciliares sistemáticas e atenção domiciliar para acamados ou pacientes com problemas crônicos compensados."
    },
    {
        "directive": "Núcleo de Apoio à Saúde da Família (NASF)",
        "target_demographic": "Equipes de Saúde da Família",
        "clinical_guideline": "Apoio matricial multiprofissional (psicólogos, fisioterapeutas, nutricionistas etc.) para ampliação da resolutividade da Atenção Básica."
    },
    {
        "directive": "Populações Específicas (Consultório na Rua / Ribeirinhas)",
        "target_demographic": "População em Situação de Rua e Ribeirinhos",
        "clinical_guideline": "Equipes itinerantes com horário flexível para prestar atenção integral a populações marginalizadas ou de difícil acesso."
    }
]

# --- 4. PNSTT (Saúde do Trabalhador) ---
pnstt_directives = [
    {
        "directive": "Notificação de Acidentes e Doenças (Visat)",
        "target_demographic": "Trabalhadores Formais e Informais",
        "clinical_guideline": "Identificação e notificação compulsória no SINAN de acidentes de trabalho (típicos e de trajeto) e Doenças Relacionadas ao Trabalho (LER/DORT, Dermatoses)."
    },
    {
        "directive": "Anamnese Ocupacional",
        "target_demographic": "Pacientes da Atenção Básica",
        "clinical_guideline": "Inclusão sistemática de perguntas sobre a ocupação atual e pregressa em todas as consultas para estabelecer o nexo causal de adoecimentos."
    },
    {
        "directive": "Transtornos Mentais Relacionados ao Trabalho",
        "target_demographic": "Trabalhadores Expostos a Risco Psicossocial",
        "clinical_guideline": "Diagnóstico e manejo de Burnout, estresse pós-traumático e alcoolismo crônico decorrentes de assédio, pressão por metas ou violência no trabalho."
    },
    {
        "directive": "Intoxicação por Agrotóxicos",
        "target_demographic": "Trabalhadores Rurais e População do Entorno",
        "clinical_guideline": "Identificação de intoxicações agudas e crônicas, notificação imediata, afastamento da exposição e articulação intersetorial para controle ambiental."
    },
    {
        "directive": "Pneumoconioses (Silicose)",
        "target_demographic": "Trabalhadores da Construção e Mineração",
        "clinical_guideline": "Afastamento imediato da exposição à poeira de sílica, acompanhamento radiológico e espirométrico, e notificação para emissão de CAT."
    }
]

# --- 5. PNSPI (Saúde da Pessoa Idosa) ---
pnspi_directives = [
    {
        "directive": "Avaliação Multidimensional (IVCF-20)",
        "target_demographic": "Pessoas com 60 anos ou mais",
        "clinical_guideline": "Aplicação do Índice de Vulnerabilidade Clínico-Funcional para classificar o risco de fragilidade (baixo, moderado, alto) e definir o plano de cuidados."
    },
    {
        "directive": "Prevenção de Quedas",
        "target_demographic": "Pessoas Idosas",
        "clinical_guideline": "Avaliação ambiental do domicílio, correção de déficits visuais, revisão de polifarmácia e estímulo ao fortalecimento muscular e equilíbrio."
    },
    {
        "directive": "Manejo da Polifarmácia",
        "target_demographic": "Idosos em uso de múltiplos medicamentos",
        "clinical_guideline": "Revisão periódica de prescrições para evitar interações medicamentosas nocivas, reações adversas e risco aumentado de quedas ou confusão mental."
    },
    {
        "directive": "Prevenção e Identificação de Violências",
        "target_demographic": "Pessoas Idosas Vulneráveis",
        "clinical_guideline": "Detecção ativa de negligência, abandono, violência física, psicológica ou patrimonial (financeira) e acionamento da rede de proteção (Disque 100, CRAS)."
    },
    {
        "directive": "Saúde Mental e Cognitiva",
        "target_demographic": "Pessoas Idosas",
        "clinical_guideline": "Rastreio e tratamento de depressão, isolamento social, e demências (Alzheimer), promovendo a manutenção da autonomia e independência funcional."
    }
]

# Mapping dictionary for the loop
policy_map = {
    "PNAISH": pnaish_directives,
    "PNAISC": pnaisc_directives,
    "PNAB": pnab_directives,
    "PNSTT": pnstt_directives,
    "PNSPI": pnspi_directives
}

def seed_all_policies():
    db = database.SessionLocal()
    
    try:
        # If you are using a generic Policy table, you might need a 'policy_name' column.
        # Assuming you modify your database.py to handle this, or we just insert into a generic Policy table.
        # For this script, we assume you have a generic table named 'PublicHealthPolicy' with a 'policy_name' column.
        
        # db.query(database.PublicHealthPolicy).delete() # Optional: clear before seeding
        
        total_count = 0
        
        for policy_name, directives in policy_map.items():
            print(f"Seeding {policy_name} database from official guidelines...")
            for item in directives:
                # IMPORTANT: Ensure your database.py has a PublicHealthPolicy model:
                # class PublicHealthPolicy(Base):
                #     __tablename__ = "public_health_policies"
                #     id = Column(Integer, primary_key=True, index=True)
                #     policy_name = Column(String, index=True)
                #     directive = Column(String)
                #     target_demographic = Column(String)
                #     clinical_guideline = Column(Text)
                
                entry = database.PublicHealthPolicy(
                    policy_name=policy_name,
                    directive=item["directive"],
                    target_demographic=item["target_demographic"],
                    clinical_guideline=item["clinical_guideline"]
                )
                db.add(entry)
                total_count += 1
                
        db.commit()
        print(f"Successfully seeded {total_count} total clinical directives into SQLite across all 5 policies.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Note: You must ensure your database.py has a 'PublicHealthPolicy' table model configured.")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_all_policies()
