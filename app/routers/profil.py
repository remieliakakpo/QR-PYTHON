from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.models.models import User, Profile, EmergencyContact
from app.schemas.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
import uuid

# On définit le router (Assure-toi de l'inclure dans main.py avec prefix="/profil")
router = APIRouter()

# --- 1. CRÉATION DU PROFIL ---
@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a déjà un profil pour éviter les doublons
    if db.query(Profile).filter(Profile.user_id == current_user.id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Un profil existe déjà pour cet utilisateur"
        )

    # Création de l'objet Profile avec les données reçues du mobile
    profile = Profile(
        id=str(uuid.uuid4()),
        qr_token=str(uuid.uuid4()), # Jeton unique qui sera dans le QR Code
        user_id=current_user.id,
        profile_type=data.profile_type,
        first_name=data.first_name,
        last_name=data.last_name,
        birth_date=data.birth_date,
        gender=data.gender,
        nationality=data.nationality,
        
        # Section Médicale 
        blood_type=data.blood_type,
        disabilities=data.disabilities,
        
        # Section École (Optionnel)
        school_name=data.school_name,
        class_name=data.class_name,
        director_name=data.director_name,
        director_phone=data.director_phone,
        parent_name=data.parent_name,
        parent_phone=data.parent_phone,
        
        # Section Véhicule
        has_vehicle=data.has_vehicle,
        vehicle_type=data.vehicle_type,
        plate=data.plate,
        brand=data.brand,
        model=data.model,
        color=data.color,
    )
    
    db.add(profile)
    db.flush() # Permet d'avoir l'ID du profil avant d'ajouter les contacts

    # Créer les contacts d'urgence liés à ce profil
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

# --- 2. RÉCUPÉRATION DU PROFIL (Pour l'utilisateur connecté) ---
@router.get("/", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return profile

# --- 3. ROUTE DE SCAN (Publique - Pour les secours) ---
@router.get("/scan/{qr_token}")
def get_profile_by_qr(qr_token: str, db: Session = Depends(get_db)):
    # On cherche le profil via le qr_token (et non l'ID utilisateur)
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profil d'urgence introuvable")

    # On retourne uniquement les infos critiques pour une intervention rapide
    return {
        "status": "emergency_data",
        "identity": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "gender": profile.gender,
            "birth_date": profile.birth_date
        },
        "medical": {
            "blood_type": profile.blood_type,
            "disabilities": profile.disabilities
        },
        "emergency_contacts": [
            {"name": c.name, "phone": c.phone, "relation": c.relation}
            for c in profile.emergency_contacts
        ],
        "vehicle": {
            "has_vehicle": profile.has_vehicle,
            "plate": profile.plate if profile.has_vehicle else None
        }
    }

# --- 4. MISE À JOUR DU PROFIL ---
@router.put("/", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # On met à jour uniquement les champs envoyés (exclude_unset=True)
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile