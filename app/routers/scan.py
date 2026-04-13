from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.models import Scan, Profile
import uuid

router = APIRouter()

# On passe en GET car un scan de QR Code ouvre une URL dans un navigateur
@router.get("/{qr_token}")
def log_and_get_profile(
    qr_token: str,
    request: Request,
    db: Session = Depends(get_db),
    lat: float = None,  # Paramètres optionnels passés dans l'URL
    lon: float = None,
):
    # 1. Chercher le profil correspondant au jeton
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # 2. Enregistrer le Scan (Historique et Géolocalisation)
    new_scan = Scan(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        latitude=lat,
        longitude=lon,
        scanner_ip=request.client.host,
        alert_sent=False,
    )
    db.add(new_scan)
    db.commit()

    # 3. Retourner les données vitales pour les secours
    # C'est ce qui s'affichera sur l'écran du secouriste
    return {
        "status": "success",
        "data": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "blood_type": profile.blood_type,
            "disabilities": profile.disabilities,
            "emergency_contacts": [
                {"name": c.name, "phone": c.phone, "relation": c.relation}
                for c in profile.emergency_contacts
            ],
            # Infos véhicule pour identification
            "vehicle": {
                "plate": profile.plate if profile.has_vehicle else None,
                "model": profile.model if profile.has_vehicle else None
            }
        }
    }