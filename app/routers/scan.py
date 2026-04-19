from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload # <--- AJOUTER joinedload ICI
from app.utils.database import get_db
from app.models.models import Scan, Profile
from pydantic import BaseModel

router = APIRouter()

class ScanVerifyRequest(BaseModel):
    token: str
    pin: str
    authority_type: str = "emergency_unit"

MASTER_CODES = {
    "POL1717": "Police Nationale",
    "AMBU1818": "Service d'Ambulance",
    "POMP2626": "Sapeurs-Pompiers",
    "MEDC3737": "Corps Médical",
}

@router.post("/verify")
def verify_scan(body: ScanVerifyRequest, db: Session = Depends(get_db)):
    clean_pin = str(body.pin).strip().upper()
    
    # --- CORRECTION ICI : Ajout de joinedload pour charger les contacts ---
    profile = db.query(Profile).options(
        joinedload(Profile.emergency_contacts)
    ).filter(
        (Profile.qr_token == body.token) | (Profile.id == body.token)
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    authority_name = MASTER_CODES.get(clean_pin)
    
    if not authority_name:
        user_pin = str(getattr(profile, 'access_code', '1234')).strip().upper()
        if clean_pin == user_pin:
            authority_name = "Accès Privé"

    if not authority_name:
        raise HTTPException(status_code=403, detail="CODE INVALIDE")

    return {
        "status": "success",
        "authority": authority_name,
        "identity": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "birth_date": profile.birth_date or "Non renseignée",
            "gender": profile.gender or "NC",
            "nationality": getattr(profile, 'nationality', 'Togolaise'),
        },
        "medical": {
            "blood_type": profile.blood_type or "NC",
            "allergies": profile.allergies or "Aucune",
            "conditions": profile.conditions or "Aucune",
            "medications": profile.medications or "Aucun",
            "disabilities": profile.disabilities or "Aucun", # Vérifie que Vercel compare bien avec "Aucun"
        },
        "emergency_contacts": [
            {
                "name": c.name, 
                "phone": c.phone, 
                "relation": c.relation
            } for c in profile.emergency_contacts
        ], # Retrait du "if" complexe, joinedload s'occupe de rendre la liste itérable
        "audit": {
            "authority": authority_name,
            "token": body.token[:8]
        }
    }