from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.utils.auth import hash_password, verify_password, create_token, get_current_user
from app.models.models import User
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
import uuid

# INITIALISATION DU ROUTEUR (Indispensable)
router = APIRouter()

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    print(f"DEBUG: Tentative d'inscription avec le numéro: {data.phone}")
    
    # Vérifier si téléphone existe déjà
    existing_user = db.query(User).filter(User.phone == data.phone).first()
    if existing_user:
        print("DEBUG: Numéro déjà utilisé")
        raise HTTPException(status_code=400, detail="Ce numéro est déjà utilisé")

    try:
        user = User(
            id=str(uuid.uuid4()),
            phone=data.phone,
            password=hash_password(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        token = create_token(user.id)
        return {"message": "Compte créé", "token": token, "user": {"id": user.id, "phone": user.phone}}
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne serveur")