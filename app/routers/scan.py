from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.models import Scan, Profile
from pydantic import BaseModel

router = APIRouter()

class MobileScanRequest(BaseModel):
    token: str
    pin: str
    authority_type: str

# --- ROUTE POUR L'ÉTAPE 5 (Récupération du QR Token) ---
@router.get("/generate/{qr_token}")
def get_qr_data(qr_token: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil SafeLife introuvable")
    
    return {
        "status": "success",
        "qr_token": qr_token,
        "qr_url": f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_token}",
        "first_name": profile.first_name,
        "last_name": profile.last_name
    }

# --- VÉRIFICATION SCAN (Secours) ---
@router.post("/verify")
def verify_mobile_scan(request: MobileScanRequest, db: Session = Depends(get_db)):
    clean_pin = str(request.pin).strip().upper()
    MASTER_CODES = ["POL1717", "AMBU1818"]

    profile = db.query(Profile).filter(
        (Profile.qr_token == request.token) | (Profile.id == request.token)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    db_pin = getattr(profile, 'access_code', None) or "1234"
    user_code = str(db_pin).strip().upper()

    if clean_pin in MASTER_CODES or clean_pin == user_code:
        return {
            "status": "success",
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "blood_type": profile.blood_type or "NC",
            "allergies": getattr(profile, 'allergies', 'AUCUNE'),
            "emergency_contact_phone": profile.emergency_contacts[0].phone if profile.emergency_contacts else "N/A"
        }

    raise HTTPException(status_code=403, detail="Code invalide")

# --- FICHE WEB ---
@router.get("/{qr_token}", response_class=HTMLResponse)
def public_profile(qr_token: str, request: Request, db: Session = Depends(get_db)):
    return HTMLResponse(content=f"<html><body>Fiche SafeLife de {qr_token}</body></html>")