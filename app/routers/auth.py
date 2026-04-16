from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

# On importe les outils de l'autre fichier et les modèles
from app.utils.database import get_db
from app.utils.auth import hash_password, verify_password, create_token
from app.models.models import User, Profile
from app.schemas.schemas import UserRegister, UserLogin

# INITIALISATION DU ROUTEUR (La ligne cruciale)
router = APIRouter()

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    # Vérification si l'utilisateur existe
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="Numéro déjà utilisé")

    try:
        user_id = str(uuid.uuid4())
        # Création de l'utilisateur
        new_user = User(
            id=user_id,
            phone=data.phone,
            password=hash_password(data.password)
        )
        db.add(new_user)

        # Création du profil obligatoire pour le QR Code
        qr_token = str(uuid.uuid4())[:8].upper()
        new_profile = Profile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            qr_token=qr_token,
            profile_type="CITIZEN",
            first_name="Utilisateur",
            last_name="SafeMe",
            birth_date="01/01/2000",
            gender="M",
            nationality="Togo",
            blood_type="NC",
            access_code="1234"
        )
        db.add(new_profile)
        
        db.commit()
        return {"status": "success", "token": create_token(user_id), "qr_token": qr_token}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    return {
        "status": "success",
        "token": create_token(user.id),
        "qr_token": user.profile.qr_token if user.profile else None
    }