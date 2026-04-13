from pydantic import BaseModel, EmailStr
from typing import Optional, List
# ─── Profil ───
class ProfileCreate(BaseModel):
    profile_type: str = "adult"
    first_name: str
    last_name: str
    birth_date: str
    gender: str
    nationality: str
    
    # MODIFICATION : On les rend optionnels car l'app mobile ne les envoie pas encore
    document_type: Optional[str] = "N/A" 
    document_number: Optional[str] = "N/A"
    
    photo_uri: Optional[str] = None
    blood_type: str
    
    # Ces champs resteront None mais doivent être présents pour la validation
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    surgeries: Optional[str] = None
    disabilities: Optional[str] = None
    
    # École
    school_name: Optional[str] = None
    class_name: Optional[str] = None
    director_name: Optional[str] = None
    director_phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    
    # Véhicule
    has_vehicle: bool = False
    vehicle_type: Optional[str] = None
    plate: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    
    # Contacts d'urgence (Obligatoire)
    emergency_contacts: List[EmergencyContactCreate]