from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scan, auth 
from app.utils.database import engine
from app.models import models
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Synchronisation DB
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Base de données SafeLife prête.")
except Exception as e:
    logger.error(f"❌ Erreur DB : {e}")

app = FastAPI(title="SafeLife API")

# CORS (Crucial pour React Native)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTAGE ---

# On enregistre les DEUX pour que ton app ne reçoive plus de 404
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(auth.router, prefix="/profil", tags=["Profil Mobile"])

# Système de Scan et génération de QR (Pour ton étape 5)
app.include_router(scan.router, prefix="/api/profile", tags=["Scan"])

@app.get("/")
def read_root():
    return {"status": "online", "project": "SafeLife"}