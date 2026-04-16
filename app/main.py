from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models import models
from pydantic import BaseModel

router = APIRouter()

# Schéma pour recevoir la requête de scan
class ScanVerifyRequest(BaseModel):
    token: str
    pin: str
    authority_type: str

@router.post("/verify")
def verify_scan(request: ScanVerifyRequest, db: Session = Depends(get_db)):
    # 1. Nettoyage du code saisi (Majuscules + suppression espaces)
    clean_pin = request.pin.strip().upper()
    
    # 2. Définition des CODES MAÎTRES (Gouvernance GRC)
    MASTER_CODES = ["POL1717", "AMBU1818"]

    # 3. Recherche du profil par son ID (le token du QR code)
    profile = db.query(models.Profile).filter(models.Profile.id == request.token).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil de la victime introuvable.")

    # 4. LOGIQUE DE DÉVERROUILLAGE
    # Cas A : C'est un code autorité
    if clean_pin in MASTER_CODES:
        # On renvoie les données directement (Accès privilégié)
        return {
            "identity": {
                "first_name": profile.first_name,
                "last_name": profile.last_name
            },
            "medical": {
                "blood_type": profile.blood_type,
                "allergies": profile.allergies,
                "treatment": profile.treatment
            },
            "emergency_contact": profile.emergency_contact_phone, # Ton champ du Step 2
            "audit": {
                "verified_by": f"Autorité ({request.authority_type})",
                "code_used": clean_pin
            }
        }

    # Cas B : C'est le code personnel de l'utilisateur
    # Note : Vérifie si ta colonne s'appelle 'access_code' ou 'pin' dans ton modèle
    if clean_pin == profile.access_code:
        return {
            "identity": {"first_name": profile.first_name, "last_name": profile.last_name},
            "medical": {"blood_type": profile.blood_type},
            "emergency_contact": profile.emergency_contact_phone,
            "audit": {"verified_by": "Code Personnel"}
        }

    # Cas C : Le code est faux
    raise HTTPException(status_code=403, detail="Code d'accès invalide.")