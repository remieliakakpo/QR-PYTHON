from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.utils.auth import hash_password, verify_password, create_token, get_current_user
from app.models.models import User
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
import uuid

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    # Vérifier si téléphone existe déjà
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="Ce numéro est déjà utilisé")

    user = User(
        id=str(uuid.uuid4()),
        phone=data.phone,
        password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return {"message": "Compte créé avec succès", "token": token, "user": user}

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Numéro ou mot de passe incorrect")

    token = create_token(user.id)
    return {"message": "Connexion réussie", "token": token, "user": user}

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user