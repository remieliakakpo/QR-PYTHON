from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

# Imports de tes outils et modèles
from app.utils.database import get_db
from app.utils.auth import hash_password, verify_password, create_token
from app.models.models import User, Profile
from app.schemas.schemas import UserRegister, UserLogin

# INITIALISATION DU ROUTEUR
router = APIRouter()

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Crée un utilisateur ET son profil SafeMe associé.
    """
    # 1. Vérification d'existence
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Ce numéro de téléphone est déjà enregistré."
        )

    try:
        # 2. Création de l'utilisateur
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            phone=data.phone,
            password=hash_password(data.password) # Hachage via utils/auth.py
        )
        db.add(new_user)

        # 3. Création du profil médical par défaut
        # Le qr_token est ce qui sera scanné en cas d'urgence
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
            blood_type="NC", # Non Communiqué par défaut
            access_code="1234", # Code PIN par défaut pour les secours
            has_vehicle=False
        )
        db.add(new_profile)
        
        db.commit()
        db.refresh(new_user)
        
        # 4. Retourne le token de session et les infos de base
        return {
            "status": "success",
            "token": create_token(new_user.id),
            "user": {
                "id": new_user.id,
                "phone": new_user.phone,
                "qr_token": qr_token
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERREUR REGISTER: {str(e)}") # Log pour Railway
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la création du compte."
        )

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Authentification et récupération du qr_token pour l'app mobile.
    """
    user = db.query(User).filter(User.phone == data.phone).first()
    
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Numéro ou mot de passe incorrect."
        )

    # Récupération sécurisée du qr_token via la relation
    qr_token = user.profile.qr_token if user.profile else None

    return {
        "status": "success",
        "token": create_token(user.id),
        "user": {
            "id": user.id,
            "phone": user.phone,
            "qr_token": qr_token
        }
    }