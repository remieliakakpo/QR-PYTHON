from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.models import Scan, Profile
from pydantic import BaseModel

# 1. Configuration du Router
router = APIRouter()

# 2. Modèle de données pour la requête mobile
class ScanVerifyRequest(BaseModel):
    token: str
    pin: str
    authority_type: str = "emergency_unit"

# 3. Codes d'unités autorisés
MASTER_CODES = {
    "POL1717": "Police Nationale",
    "AMBU1818": "Service d'Ambulance",
    "POMP2626": "Sapeurs-Pompiers",
    "MEDC3737": "Corps Médical",
}

@router.get("/{qr_token}", response_class=HTMLResponse)
def public_profile(qr_token: str, request: Request, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return HTMLResponse(content=f"<html><body><h1>Profil de {profile.first_name}</h1><p>Utilisez l'application SafeLife pour déverrouiller les données vitales.</p></body></html>")

@router.post("/verify")
def verify_scan(body: ScanVerifyRequest, db: Session = Depends(get_db)):
    clean_pin = str(body.pin).strip().upper()
    
    # Recherche par qr_token ou ID
    profile = db.query(Profile).filter(
        (Profile.qr_token == body.token) | (Profile.id == body.token)
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    authority_name = MASTER_CODES.get(clean_pin)
    
    # Vérification code personnel si pas de code maître
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
            "disabilities": profile.disabilities or "Aucun",
        },
        "vehicle": {
            "has_vehicle": getattr(profile, 'has_vehicle', False),
            "type": getattr(profile, 'vehicle_type', None),
            "plate": getattr(profile, 'plate', None),
            "brand": getattr(profile, 'brand', None),
            "model": getattr(profile, 'model', None),
        },
        "emergency_contacts": [
            {"name": c.name, "phone": c.phone, "relation": c.relation}
            for c in profile.emergency_contacts
        ] if profile.emergency_contacts else [],
        "audit": {
            "authority": authority_name,
            "token": body.token[:8]
        }
    }