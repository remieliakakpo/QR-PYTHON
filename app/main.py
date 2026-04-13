from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text # Import ajouté
from app.utils.database import engine
from app.models import models
# On importe les routers
from app.routers import auth, profil, scan

# 1. Création des tables dans la base de données
models.Base.metadata.create_all(bind=engine)

# --- DEBUT DU SCRIPT DE REPARATION SQL ---
def repair_database():
    with engine.connect() as connection:
        try:
            # On force le passage des colonnes document en "nullable"
            connection.execute(text("ALTER TABLE profiles ALTER COLUMN document_type DROP NOT NULL"))
            connection.execute(text("ALTER TABLE profiles ALTER COLUMN document_number DROP NOT NULL"))
            connection.commit()
            print("--- REPARATION : Colonnes document rendues optionnelles avec succès ! ---")
        except Exception as e:
            # Si les colonnes n'existent pas encore ou sont déjà à jour, on ignore l'erreur
            print(f"--- REPARATION : Info ou Erreur : {e} ---")

# On lance la réparation juste après la création des tables
repair_database()
# --- FIN DU SCRIPT DE REPARATION SQL ---

# 2. Initialisation de l'application FastAPI
app = FastAPI(title="SafeLife", version="1.0.0")

# 3. Configuration du CORS (très important pour le mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Inclusion des routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profil.router, prefix="/profil", tags=["profil"])
app.include_router(scan.router, prefix="/scan", tags=["scan"])

@app.get("/")
def root():
    return {
        "message": "SafeLife API fonctionne !", 
        "version": "1.0.0",
        "status": "online"
    }