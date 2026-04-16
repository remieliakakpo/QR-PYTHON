from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scan  # Assure-toi que ton fichier scan.py est dans app/routers/
from app.utils.database import engine
from app.models import models

# Création des tables dans la base de données (Supabase) si elles n'existent pas
models.Base.metadata.create_all(bind=engine)

# --- L'INSTANCE CRITIQUE POUR RAILWAY ---
# C'est cette variable "app" que le serveur Uvicorn recherche
app = FastAPI(
    title="SafeMe API",
    description="Backend de gestion d'urgence pour le projet SafeMe Togo",
    version="1.0.0"
)

# --- CONFIGURATION CORS ---
# Indispensable pour que ton application mobile (React Native) ne soit pas bloquée
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet à toutes les origines de se connecter
    allow_credentials=True,
    allow_methods=["*"],  # Autorise GET, POST, etc.
    allow_headers=["*"],
)

# --- INCLUSION DES ROUTEURS ---
# On attache les routes définies dans scan.py (HTML et JSON)
# Elles seront accessibles via https://safelife.up.railway.app/scan/...
app.include_router(scan.router, prefix="/scan", tags=["Scan & Urgence"])

# Route de test pour vérifier que le serveur est en ligne
@app.get("/")
def health_check():
    return {
        "status": "online",
        "project": "SafeMe Togo",
        "author": "Rémi Eli Kokou"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)