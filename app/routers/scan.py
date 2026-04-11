from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.models import Scan, Profile
import uuid

router = APIRouter()

@router.post("/{qr_token}")
def log_scan(
    qr_token: str,
    request: Request,
    db: Session = Depends(get_db),
    latitude: float = None,
    longitude: float = None,
):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        return {"error": "Profil introuvable"}

    scan = Scan(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        latitude=latitude,
        longitude=longitude,
        scanner_ip=request.client.host,
        alert_sent=False,
    )
    db.add(scan)
    db.commit()

    return {"message": "Scan enregistré", "profile_id": profile.id}