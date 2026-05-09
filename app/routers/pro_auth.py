# backend/app/routers/pro_auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import hashlib

router = APIRouter(prefix="/pro", tags=["pro"])

SECRET = "safelife_pro_secret_2024"

# ─── Utilisateurs pro prédéfinis ─────────────────────────────
# Mot de passe par défaut : safelife2024
# Hash SHA256 de "safelife2024"
PWD_HASH = hashlib.sha256("safelife2024".encode()).hexdigest()

PRO_USERS = {
    "SAMU-CHU-0812":    { "nom": "Dr. Ama Koffi",   "role": "SAMU",      "unite": "CHU Sylvanus Olympio", "password_hash": PWD_HASH },
    "POMPIERS-LME-118": { "nom": "Chef Kokou Doe",  "role": "Pompiers",  "unite": "Caserne de Lomé",      "password_hash": PWD_HASH },
    "POLICE-LME-4471":  { "nom": "Insp. Mensah",    "role": "Police",    "unite": "Commissariat Lomé",    "password_hash": PWD_HASH },
    "AMBU-BE-0021":     { "nom": "Ambu Togbé",      "role": "Ambulance", "unite": "Hôpital de Bè",        "password_hash": PWD_HASH },
    "GEND-KPM-1133":    { "nom": "Adj. Agbeko",     "role": "Gendarmerie","unite": "Brigade Kpalimé",     "password_hash": PWD_HASH },
}

class LoginRequest(BaseModel):
    code:     str
    password: str

@router.post("/login")
def login_pro(data: LoginRequest):
    code = data.code.upper().strip()
    user = PRO_USERS.get(code)

    if not user:
        raise HTTPException(status_code=401, detail="Code institutionnel invalide")

    pwd_hash = hashlib.sha256(data.password.encode()).hexdigest()
    if pwd_hash != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")

    token = jwt.encode(
        {
            "sub":  code,
            "nom":  user["nom"],
            "role": user["role"],
            "exp":  datetime.utcnow() + timedelta(hours=12),
        },
        SECRET,
        algorithm="HS256",
    )

    return {
        "token": token,
        "user": {
            "code":        code,
            "nom":         user["nom"],
            "role":        user["role"],
            "unite":       user["unite"],
            "institution": user["unite"],
        },
    }