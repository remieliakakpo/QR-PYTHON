from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scan, auth, profil
from app.utils.database import engine
from app.models import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Base de données SafeLife prête.")
except Exception as e:
    logger.error(f"❌ Erreur DB : {e}")

app = FastAPI(title="SafeLife API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,   prefix="/auth",   tags=["Auth"])
app.include_router(profil.router, prefix="/profil", tags=["Profil"])
app.include_router(scan.router,   prefix="/scan",   tags=["Scan"])

@app.get("/")
def read_root():
    return {"status": "online", "project": "SafeLife"}