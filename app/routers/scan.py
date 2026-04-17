from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.models import Scan, Profile
from pydantic import BaseModel
import uuid

router = APIRouter()

class MobileScanRequest(BaseModel):
    token: str
    pin: str
    authority_type: str

@router.post("/verify")
def verify_mobile_scan(request: MobileScanRequest, db: Session = Depends(get_db)):
    # 1. Nettoyage du code saisi
    clean_pin = str(request.pin).strip().upper()
    MASTER_CODES = ["POL1717", "AMBU1818"]

    # 2. Recherche du profil (par QR Token ou ID)
    profile = db.query(Profile).filter(
        (Profile.qr_token == request.token) | (Profile.id == request.token)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # 3. Récupération du code personnel
    db_pin = getattr(profile, 'access_code', None) or "1234"
    user_code = str(db_pin).strip().upper()

    # 4. Vérification et Renvoi des données
    if clean_pin in MASTER_CODES or clean_pin == user_code:
        # On renvoie tout au premier niveau (Flat JSON) pour l'app mobile
        return {
            "status": "success",
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "blood_type": profile.blood_type or "NC",
            "allergies": getattr(profile, 'allergies', 'AUCUNE'),
            "conditions": getattr(profile, 'conditions', 'AUCUNE'),
            "medications": getattr(profile, 'medications', 'AUCUN'),
            "handicaps": getattr(profile, 'handicaps', 'AUCUN'),
            "emergency_contact_phone": profile.emergency_contacts[0].phone if profile.emergency_contacts else "N/A",
            "emergency_contact_name": profile.emergency_contacts[0].name if profile.emergency_contacts else "Contact",
            "method": "MASTER_CODE" if clean_pin in MASTER_CODES else "USER_PIN"
        }

    raise HTTPException(status_code=403, detail="Code d'accès invalide")

@router.get("/{qr_token}", response_class=HTMLResponse)
def log_and_display_profile(qr_token: str, request: Request, db: Session = Depends(get_db)):
    # Garde ici ton code HTML actuel, il est parfait pour le navigateur !
    pass