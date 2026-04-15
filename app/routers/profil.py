from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.models.models import User, Profile, EmergencyContact
from app.schemas.schemas import ProfileCreate, ProfileResponse
import uuid

router = APIRouter()

# --- 1. SCAN INITIAL (Public) ---
@router.get("/{profile_id}")
def get_profile_status(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # On confirme juste l'identité pour rassurer le secouriste
    return {
        "id": profile.id,
        "owner_name": f"{profile.first_name} {profile.last_name}",
        "status": "locked" 
    }

# --- 2. DÉVERROUILLAGE UNIQUE (Le code valide l'accès à TOUT) ---
@router.post("/{profile_id}/unlock")
def unlock_profile(profile_id: str, access_code: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    
    if profile.access_code != access_code:
        raise HTTPException(status_code=401, detail="Code d'accès invalide")

    # Une fois déverrouillé, on donne toutes les infos nécessaires aux secours
    return {
        "status": "unlocked",
        "identity": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "birth_date": profile.birth_date
        },
        "medical": {
            "blood_type": profile.blood_type,
            "disabilities": profile.disabilities,
        },
        "contacts": [
            {"name": c.name, "phone": c.phone, "relation": c.relation}
            for c in profile.emergency_contacts
        ],
        "school": {
            "parent_name": profile.parent_name,
            "parent_phone": profile.parent_phone
        } if profile.profile_type == "student" else None
    }

# --- 3. CRÉATION DU PROFIL ---
@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(data: ProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(Profile).filter(Profile.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Un profil existe déjà")

    profile = Profile(
        id=str(uuid.uuid4()),
        qr_token=str(uuid.uuid4()),
        user_id=current_user.id,
        **data.dict(exclude={'emergency_contacts'}), # On injecte les données proprement
        access_code=getattr(data, 'access_code', '1234')
    )
    
    db.add(profile)
    db.flush()

    for contact in data.emergency_contacts:
        db.add(EmergencyContact(id=str(uuid.uuid4()), profile_id=profile.id, **contact.dict()))

    db.commit()
    db.refresh(profile)
    return profile

# --- 4. MON PROFIL (Utilisateur connecté) ---
@router.get("/me", response_model=ProfileResponse)
def get_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return profile