from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.models.models import User, Profile, EmergencyContact
from app.schemas.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
import uuid

router = APIRouter()

@router.post("/", response_model=ProfileResponse)
def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier si profil existe déjà
    if db.query(Profile).filter(Profile.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Un profil existe déjà pour cet utilisateur")

    # Créer le profil
    profile = Profile(
        id=str(uuid.uuid4()),
        qr_token=str(uuid.uuid4()),
        user_id=current_user.id,
        profile_type=data.profile_type,
        first_name=data.first_name,
        last_name=data.last_name,
        birth_date=data.birth_date,
        gender=data.gender,
        nationality=data.nationality,
        document_type=data.document_type,
        document_number=data.document_number,
        photo_uri=data.photo_uri,
        blood_type=data.blood_type,
        allergies=data.allergies,
        conditions=data.conditions,
        medications=data.medications,
        surgeries=data.surgeries,
        disabilities=data.disabilities,
        school_name=data.school_name,
        class_name=data.class_name,
        director_name=data.director_name,
        director_phone=data.director_phone,
        parent_name=data.parent_name,
        parent_phone=data.parent_phone,
        has_vehicle=data.has_vehicle,
        vehicle_type=data.vehicle_type,
        plate=data.plate,
        brand=data.brand,
        model=data.model,
        color=data.color,
    )
    db.add(profile)
    db.flush()

    # Créer les contacts d'urgence
    for contact in data.emergency_contacts:
        db.add(EmergencyContact(
            id=str(uuid.uuid4()),
            profile_id=profile.id,
            name=contact.name,
            phone=contact.phone,
            relation=contact.relation,
        ))

    db.commit()
    db.refresh(profile)
    return profile

@router.get("/", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return profile

@router.get("/scan/{qr_token}")
def get_profile_by_qr(qr_token: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    return {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "birth_date": profile.birth_date,
        "gender": profile.gender,
        "blood_type": profile.blood_type,
        "allergies": profile.allergies,
        "conditions": profile.conditions,
        "medications": profile.medications,
        "has_vehicle": profile.has_vehicle,
        "vehicle_type": profile.vehicle_type,
        "plate": profile.plate,
        "profile_type": profile.profile_type,
        "school_name": profile.school_name,
        "class_name": profile.class_name,
        "director_name": profile.director_name,
        "director_phone": profile.director_phone,
        "parent_name": profile.parent_name,
        "parent_phone": profile.parent_phone,
        "emergency_contacts": [
            {"name": c.name, "phone": c.phone, "relation": c.relation}
            for c in profile.emergency_contacts
        ],
    }

@router.put("/", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile