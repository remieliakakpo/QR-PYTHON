from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scan, auth 
from app.utils.database import engine
from app.models import models
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Synchronisation de la base de données
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Base de données synchronisée avec succès.")
except Exception as e:
    logger.error(f"❌ Erreur de synchronisation DB : {e}")

# --- INITIALISATION DE L'APP ---
app = FastAPI(
    title="SafeMe API",
    description="Système de GRC et Urgence Médicale - Togo",
    version="1.1.0",
    redirect_slashes=True 
)

# --- CONFIGURATION CORS (CRITIQUE POUR REACT NATIVE) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUSION DES MODULES (ROUTERS) ---
# On ajuste les préfixes pour correspondre aux appels "404" de ton application mobile

app.include_router(auth.router, prefix="/auth", tags=["Authentification"])


app.include_router(scan.router, prefix="/api/profile/scan", tags=["Système de Scan"])

# --- ROUTES DE TEST ---
@app.get("/")
def home():
    return {
        "status": "online",
        "project": "SafeMe",
        "version": "1.1.0",
        "endpoints": ["/auth", "/api/profile/scan"]
    }

@app.get("/health")
def health_check():
    return {"check": "database & api connection ok"}

if __name__ == "__main__":
    import uvicorn
    import os
    # Utilisation du port dynamique de Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)