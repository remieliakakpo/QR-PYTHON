from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, profil, scan
from app.utils.database import engine
from app.models import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SafeLife", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profil.router, prefix="/profil", tags=["profil"])
app.include_router(scan.router, prefix="/scan", tags=["scan"])

@app.get("/")
def root():
    return {"message": "SafeLife API fonctionne !", "version": "1.0.0"}