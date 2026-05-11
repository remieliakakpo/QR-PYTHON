from fastapi import FastAPI
from app.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scan, auth, profil
from app.database import engine, Base, get_db
from .routers import accidents
from .routers import pro_auth
from .routers import alertes
import logging
from app.routers.alertes import AlerteEvent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Base de données SafeLife prête.")
except Exception as e:
    logger.error(f"❌ Erreur DB : {e}")

app = FastAPI(title="SafeLife API")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Démarrage de l'application SafeLife...")
    init_db()
    logger.info("✅ Base de données initialisée.")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables créées ou déjà existantes.")

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
app.include_router(accidents.router)
app.include_router(pro_auth.router)
app.include_router(alertes.router)

@app.get("/")
def read_root():
    return {"status": "online", "project": "SafeLife"}