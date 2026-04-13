from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.database import engine
from app.models import models
# On importe les routers
from app.routers import auth, profil, scan

# 1. Création des tables dans la base de données
models.Base.metadata.create_all(bind=engine)

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
# On utilise 'profil' (ton fichier profil.py) pour gérer tout ce qui touche au profil
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