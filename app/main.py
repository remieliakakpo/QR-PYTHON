from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scan, auth  # Vérifie que ces fichiers existent dans app/routers/
from app.utils.database import engine
from app.models import models
import logging

# Configuration des logs pour voir ce qui se passe sur Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Synchronisation de la base de données (Supabase/PostgreSQL)
# Cela crée les tables User, Profile, Scan, etc., si elles n'existent pas
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
    # redirect_slashes=True aide à éviter les 404 si l'app mobile ajoute un "/" à la fin de l'URL
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

# Les routes d'authentification (Register, Login, Me)
# URL de base : https://safelife.up.railway.app/auth/register
app.include_router(auth.router, prefix="/auth", tags=["Authentification"])

# Les routes de scan et affichage profil
# URL de base : https://safelife.up.railway.app/scan/verify
app.include_router(scan.router, prefix="/scan", tags=["Système de Scan"])

# --- ROUTES DE TEST ---
@app.get("/")
def home():
    return {
        "status": "online",
        "project": "SafeMe",
        "version": "1.1.0",
        "endpoints": ["/auth", "/scan"]
    }

@app.get("/health")
def health_check():
    return {"check": "database & api connection ok"}

if __name__ == "__main__":
    import uvicorn
    # Le port est récupéré dynamiquement par Railway via la variable d'environnement
    uvicorn.run(app, host="0.0.0.0", port=8000)