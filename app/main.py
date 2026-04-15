from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.utils.database import engine
from app.models import models
from app.routers import auth, profil, scan, emergency 

# 1. Création des tables de base (via SQLAlchemy)
models.Base.metadata.create_all(bind=engine)

def setup_database():
    with engine.connect() as connection:
        # A. Activation de PostGIS
        try:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            connection.commit()
            print("--- DATABASE : Extension PostGIS OK ---")
        except Exception as e:
            print(f"--- DATABASE : Erreur PostGIS : {e} ---")

        # B. Mise à jour automatique de la table PROFILES (access_code + documents)
        try:
            # On tente d'ajouter access_code (ignoré si déjà présent)
            connection.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS access_code VARCHAR DEFAULT '1234'"))
            # On rend les documents optionnels
            connection.execute(text("ALTER TABLE profiles ALTER COLUMN document_type DROP NOT NULL"))
            connection.execute(text("ALTER TABLE profiles ALTER COLUMN document_number DROP NOT NULL"))
            connection.commit()
            print("--- REPARATION : Table Profiles mise à jour ---")
        except Exception as e:
            print(f"--- REPARATION : Info Profiles : {e} ---")

        # C. Configuration spatiale pour MEDICAL_FACILITIES
        try:
            # 1. Ajout de la colonne géographique PostGIS si elle n'existe pas
            connection.execute(text("ALTER TABLE medical_facilities ADD COLUMN IF NOT EXISTS location GEOGRAPHY(Point, 4326)"))
            
            # 2. Vérification si la table est vide pour insérer les hôpitaux du Togo
            count = connection.execute(text("SELECT COUNT(*) FROM medical_facilities")).fetchone()[0]
            if count == 0:
                print("--- DATABASE : Insertion des hôpitaux de Lomé... ---")
                connection.execute(text("""
                    INSERT INTO medical_facilities (name, phone, latitude, longitude, location) VALUES
                    ('Hôpital Dogta-Lafiè', '+22822530100', 6.2085, 1.2015, ST_SetSRID(ST_Point(1.2015, 6.2085), 4326)),
                    ('CHU Sylvanus Olympio', '+22822212501', 6.1303, 1.2211, ST_SetSRID(ST_Point(1.2211, 6.1303), 4326)),
                    ('CHU Campus', '+22822254739', 6.1667, 1.2167, ST_SetSRID(ST_Point(1.2167, 6.1667), 4326))
                """))
            else:
                # 3. On s'assure que la colonne location est bien synchronisée avec lat/lon
                connection.execute(text("UPDATE medical_facilities SET location = ST_SetSRID(ST_Point(longitude, latitude), 4326) WHERE location IS NULL"))
            
            connection.commit()
            print("--- DATABASE : Géolocalisation PostGIS opérationnelle ---")
        except Exception as e:
            print(f"--- DATABASE : Erreur spatialisation : {e} ---")

# Lancement de l'initialisation
setup_database()

app = FastAPI(title="SafeLife", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profil.router, prefix="/profil", tags=["profil"])
app.include_router(scan.router, prefix="/scan", tags=["scan"])
app.include_router(emergency.router, prefix="/emergency", tags=["emergency"])

@app.get("/")
def root():
    return {
        "message": "SafeLife API (Togo Edition) fonctionne !", 
        "version": "1.1.0",
        "postgis_ready": True,
        "status": "online"
    }