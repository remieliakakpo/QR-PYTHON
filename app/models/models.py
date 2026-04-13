from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id         = Column(String, primary_key=True, default=generate_uuid)
    phone      = Column(String, unique=True, index=True, nullable=False)
    password   = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    profile = relationship("Profile", back_populates="user", uselist=False)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    qr_token = Column(String, unique=True, default=generate_uuid)
    profile_type = Column(String, nullable=False)

    # Identité
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    nationality = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    document_number = Column(String, nullable=True)
    photo_uri = Column(String, nullable=True)

    # Médical
    blood_type = Column(String, nullable=False)
    allergies = Column(String, nullable=True)
    conditions = Column(String, nullable=True)
    medications = Column(String, nullable=True)
    surgeries = Column(String, nullable=True)
    disabilities = Column(String, nullable=True)

    # École
    school_name = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    director_name = Column(String, nullable=True)
    director_phone = Column(String, nullable=True)
    parent_name = Column(String, nullable=True)
    parent_phone = Column(String, nullable=True)

    # Véhicule
    has_vehicle = Column(Boolean, default=False)
    vehicle_type = Column(String, nullable=True)
    plate = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    color = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    user = relationship("User", back_populates="profile")
    emergency_contacts = relationship("EmergencyContact", back_populates="profile")
    scans = relationship("Scan", back_populates="profile")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    relation = Column(String, nullable=True)

    profile_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    profile = relationship("Profile", back_populates="emergency_contacts")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=generate_uuid)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    scanner_ip = Column(String, nullable=True)
    alert_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    profile_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    profile = relationship("Profile", back_populates="scans")