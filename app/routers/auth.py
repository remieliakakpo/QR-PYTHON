from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.utils.auth import hash_password, verify_password, create_token, get_current_user
from app.models.models import User, Profile  
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
import uuid

# INITIALISATION DU ROUTEUR
router = APIRouter()

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    print(f"DEBUG: Tentative d'inscription avec le numéro: {data.phone}")
    
    # 1. Vérifier si téléphone existe déjà
    existing_user = db.query(User).filter(User.phone == data.phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Ce numéro est déjà utilisé")

    try:
        # 2. Création de l'utilisateur
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            phone=data.phone,
            password=hash_password(data.password),
        )
        db.add(user)
        
        # 3. CRÉATION DU PROFIL (Indispensable pour le QR Code)
        # On génère un token court de 8 caractères pour le QR Code
        generated_qr_token = str(uuid.uuid4())[:8].upper()
        
        new_profile = Profile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            qr_token=generated_qr_token,
            first_name="Utilisateur", # Valeur par défaut avant modification
            last_name="SafeMe",
            blood_type="NC",
            access_code="1234" # Code par défaut pour le déverrouillage
        )
        db.add(new_profile)

        # 4. Enregistrement final
        db.commit()
        db.refresh(user)
        
        token = create_token(user.id)
        
        # On renvoie le qr_token à l'application mobile pour qu'elle puisse l'afficher
        return {
            "message": "Compte créé", 
            "token": token, 
            "user": {
                "id": user.id, 
                "phone": user.phone,
                "qr_token": generated_qr_token # L'app mobile en a besoin pour le QR
            }
        }
        
    except Exception as e:
        db.rollback() # Annule tout en cas d'erreur
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")