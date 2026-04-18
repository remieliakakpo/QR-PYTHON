from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.models import Scan, Profile
from pydantic import BaseModel
import uuid

# 1. Définition du router
router = APIRouter()

# 2. Modèle de données pour la vérification
class ScanVerifyRequest(BaseModel):
    token: str
    pin: str
    authority_type: str = "emergency_unit"

# 3. Codes maîtres
MASTER_CODES = {
    "POL1717": "Police Nationale",
    "AMBU1818": "Service d'Ambulance",
    "POMP2626": "Sapeurs-Pompiers",
    "MEDC3737": "Corps Médical",
}

# 4. Route pour l'affichage de la page Web (quand on scanne avec un téléphone classique)
@router.get("/{qr_token}", response_class=HTMLResponse)
def public_profile(qr_token: str, request: Request, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    
    # Code pour l'affichage HTML (on pourra le remettre après si besoin)
    return HTMLResponse(content=f"<h1>Profil de {profile.first_name}</h1><p>Scannez via l'app SafeLife pour plus d'infos.</p>")

# 5. Route pour le déverrouillage (utilisée par ton application mobile)
@router.post("/verify")
def verify_scan(body: ScanVerifyRequest, db: Session = Depends(get_db)):
    # Nettoyage du code
    clean_pin = str(body.pin).strip().upper()
    
    # Recherche du profil
    profile = db.query(Profile).filter(Profile.qr_token == body.token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # Vérification du code
    authority_name = MASTER_CODES.get(clean_pin)
    
    if not authority_name:
        # Vérification du code PIN personnel si ce n'est pas un code maître
        user_pin = str(getattr(profile, 'access_code', '1234')).strip().upper()
        if clean_pin == user_pin:
            authority_name = "Accès Privé"

    if not authority_name:
        raise HTTPException(status_code=403, detail="CODE INVALIDE POUR CETTE UNITE")

    # Retour des informations au format attendu par ScanResultScreen.tsx
    return {
        "status": "success",
        "authority": authority_name,
        "identity": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "birth_date": profile.birth_date,
            "gender": profile.gender,
            "nationality": getattr(profile, 'nationality', 'TG'),
        },
        "medical": {
            "blood_type": profile.blood_type or "NC",
            "allergies": profile.allergies or "Aucune",
            "conditions": profile.conditions or "Aucune",
            "medications": profile.medications or "Aucun",
            "disabilities": profile.disabilities or "Aucun",
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