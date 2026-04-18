from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.models.models import Profile
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Schéma de données pour la réception
class ProfileCreate(BaseModel):
    first_name: str
    last_name: str
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    access_code: Optional[str] = "1234"

@router.post("/")
def create_or_update_profile(
    profile_data: ProfileCreate, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    # 1. On cherche si un profil existe déjà pour cet utilisateur
    # Note : current_user est l'ID string récupéré via le token
    existing_profile = db.query(Profile).filter(Profile.user_id == current_user).first()

    if existing_profile:
        # --- LOGIQUE DE MISE À JOUR ---
        existing_profile.first_name = profile_data.first_name
        existing_profile.last_name = profile_data.last_name
        existing_profile.blood_type = profile_data.blood_type
        existing_profile.allergies = profile_data.allergies
        existing_profile.conditions = profile_data.conditions
        existing_profile.medications = profile_data.medications
        existing_profile.access_code = profile_data.access_code
        
        db.commit()
        db.refresh(existing_profile)
        
        return {
            "status": "updated",
            "message": "Profil mis à jour avec succès",
            "qr_token": existing_profile.qr_token
        }

    # --- LOGIQUE DE CRÉATION (Si aucun profil n'existe) ---
    new_qr_token = str(uuid.uuid4())[:8].upper() # Génère un code court unique (ex: A1B2C3D4)
    
    new_profile = Profile(
        user_id=current_user,
        qr_token=new_qr_token,
        **profile_data.dict()
    )
    
    try:
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return {
            "status": "created",
            "message": "Profil créé avec succès",
            "qr_token": new_qr_token
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création : {str(e)}")