from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration (SQLite)
DATABASE_URL = "sqlite:///./medical.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# --- Models ---

class SAEDiagnostic(Base):
    __tablename__ = "sae_diagnostics"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    description_en = Column(Text, nullable=False)
    description_pt = Column(Text, nullable=False)
    intervention_en = Column(Text, nullable=False)
    intervention_pt = Column(Text, nullable=False)
    outcome_en = Column(Text, nullable=False)
    outcome_pt = Column(Text, nullable=False)


class PNAISMPolicy(Base):
    __tablename__ = "pnaism_policies"

    id = Column(Integer, primary_key=True, index=True)
    directive = Column(String, nullable=False)
    target_demographic = Column(String, nullable=False)
    clinical_guideline = Column(Text, nullable=False)


class PublicHealthPolicy(Base):
    __tablename__ = "public_health_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String, index=True, nullable=False)  # e.g., 'PNAISH', 'PNAISC', 'PNAB', 'PNSTT', 'PNSPI'
    directive = Column(String, nullable=False)
    target_demographic = Column(String, nullable=False)
    clinical_guideline = Column(Text, nullable=False)


# Utility function to create all tables
def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
