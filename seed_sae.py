import csv
import database

# Ensure tables exist
database.Base.metadata.create_all(bind=database.engine)

CSV_FILE = "sae_bilingual_final.csv"

def seed_database():
    db = database.SessionLocal()
    
    # Clear existing entries to prevent duplicates
    db.query(database.SAEDiagnostic).delete()
    db.commit()

    print(f"Reading from {CSV_FILE}...")
    
    count = 0
    seen_codes = set() # This will track and block duplicates
    
    try:
        with open(CSV_FILE, mode="r", encoding="utf-8-sig") as file:
            # Auto-detect if the user pasted from Excel (tabs) or Notepad (commas)
            first_line = file.readline()
            file.seek(0)
            detected_delimiter = '\t' if '\t' in first_line else ','
            
            reader = csv.DictReader(file, delimiter=detected_delimiter)
            
            # Force-strip any invisible spaces or breaks from the column names
            reader.fieldnames = [str(field).strip() for field in reader.fieldnames]

            for row in reader:
                code = row["code"].strip().zfill(5)
                
                # If we already seeded this code, skip it!
                if code in seen_codes:
                    continue
                seen_codes.add(code)
                
                entry = database.SAEDiagnostic(
                    code=code,
                    description_en=row["description_en"].strip(),
                    description_pt=row["description_pt"].strip(),
                    intervention_en=row["intervention_en"].strip(),
                    intervention_pt=row["intervention_pt"].strip(),
                    outcome_en=row["outcome_en"].strip(),
                    outcome_pt=row["outcome_pt"].strip()
                )
                db.add(entry)
                count += 1
            
            db.commit()
            print(f"Successfully seeded {count} unique bilingual clinical records into SQLite.")

    except FileNotFoundError:
        print(f"Error: {CSV_FILE} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
