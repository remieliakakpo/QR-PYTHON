from pydantic import BaseModel, EmailStr
from typing import Optional, List

# ─── Auth ───
class UserRegister(BaseModel):
    email: EmailStr
    phone: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    phone: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    message: str
    token: str
    user: UserResponse

# ─── Contacts ───
class EmergencyContactCreate(BaseModel):
    name: str
    phone: str
    relation: Optional[str] = None

class EmergencyContactResponse(BaseModel):
    id: str
    name: str
    phone: str
    relation: Optional[str] = None

    class Config:
        from_attributes = True

# ─── Profil ───
class ProfileCreate(BaseModel):
    profile_type: str = "adult"
    first_name: str
    last_name: str
    birth_date: str
    gender: str
    nationality: str
    document_type: str
    document_number: str
    photo_uri: Optional[str] = None
    blood_type: str
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    surgeries: Optional[str] = None
    disabilities: Optional[str] = None
    school_name: Optional[str] = None
    class_name: Optional[str] = None
    director_name: Optional[str] = None
    director_phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    has_vehicle: bool = False
    vehicle_type: Optional[str] = None
    plate: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    emergency_contacts: List[EmergencyContactCreate]

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    surgeries: Optional[str] = None
    disabilities: Optional[str] = None
    school_name: Optional[str] = None
    class_name: Optional[str] = None
    director_name: Optional[str] = None
    director_phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    has_vehicle: Optional[bool] = None
    vehicle_type: Optional[str] = None
    plate: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    qr_token: str
    profile_type: str
    first_name: str
    last_name: str
    birth_date: str
    gender: str
    nationality: str
    document_type: str
    document_number: str
    blood_type: str
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    has_vehicle: bool
    vehicle_type: Optional[str] = None
    plate: Optional[str] = None
    school_name: Optional[str] = None
    class_name: Optional[str] = None
    director_name: Optional[str] = None
    director_phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    emergency_contacts: List[EmergencyContactResponse] = []

    class Config:
        from_attributes = True