from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import os

# 1. CONFIGURATION DU HACHAGE
# On utilise l'algorithme 'bcrypt' (standard pour la cybersécurité en Master 2)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. PARAMÈTRES DU TOKEN (JWT)
# Le SECRET_KEY permet de signer tes tokens pour qu'ils ne soient pas falsifiables
SECRET_KEY = "VOTRE_CLE_TRES_SECURISE_A_CHANGER" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# --- FONCTIONS POUR LE MOT DE PASSE ---

def hash_password(password: str) -> str:
    """Transforme le mot de passe en texte illisible (hachage) pour la DB."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare un mot de passe saisi avec celui stocké en base de données."""
    return pwd_context.verify(plain_password, hashed_password)

# --- FONCTIONS POUR LE TOKEN DE CONNEXION ---

def create_token(user_id: str) -> str:
    """Génère un jeton JWT qui expire dans 7 jours."""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # Le 'sub' (subject) contient l'ID de l'utilisateur
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Vérifie si un token est valide et retourne l'ID de l'utilisateur."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
    
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Pour l'instant, on laisse passer pour débloquer le Step 5
    return {"user": "active"}