import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_
import database

app = FastAPI(
    title="Clinical Reference API & Dashboard",
    description="Bilingual SAE Diagnostics and Brazilian Public Health Policies",
    docs_url=None,      # Kills the public /docs testing page
    redoc_url=None,     # Kills the alternative /redoc page
    openapi_url=None    # Hides the API schema mapping from scrapers
)

# Securely mount the 'pdfs' directory so files can be accessed at /docs/filename.pdf
app.mount("/docs", StaticFiles(directory="pdfs"), name="docs")

# Dependency to get the DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Serve Frontend ---
@app.get("/", response_class=FileResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="index.html not found on server.")
    return FileResponse(html_path)

# --- SAE Diagnostics Keyword & Code Search ---
@app.get("/sae/search")
def search_sae(q: str, db: Session = Depends(get_db)):
    search_term = f"%{q.strip()}%"
    
    # Search across the code, Portuguese description, and English description
    results = db.query(database.SAEDiagnostic).filter(
        or_(
            database.SAEDiagnostic.code.ilike(search_term),
            database.SAEDiagnostic.description_pt.ilike(search_term),
            database.SAEDiagnostic.description_en.ilike(search_term)
        )
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"Nenhum diagnóstico encontrado para a busca: '{q}'")
    return results

# --- PNAISM Endpoint ---
@app.get("/pnaism/")
def get_pnaism_policies(db: Session = Depends(get_db)):
    results = db.query(database.PNAISMPolicy).all()
    if not results:
        raise HTTPException(status_code=404, detail="No PNAISM records found.")
    return results

# --- Unified Public Health Policies Endpoint ---
@app.get("/policy/{policy_name}")
def get_public_health_policy(policy_name: str, db: Session = Depends(get_db)):
    name_clean = policy_name.strip().upper()
    
    # Allow querying PNAISM via the unified endpoint as well
    if name_clean == "PNAISM":
        results = db.query(database.PNAISMPolicy).all()
        return [
            {
                "id": r.id,
                "policy_name": "PNAISM",
                "directive": r.directive,
                "target_demographic": r.target_demographic,
                "clinical_guideline": r.clinical_guideline
            }
            for r in results
        ]

    results = db.query(database.PublicHealthPolicy).filter(
        database.PublicHealthPolicy.policy_name == name_clean
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No directives found for policy: {name_clean}")
    return results
