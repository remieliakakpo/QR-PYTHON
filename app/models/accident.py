# backend/app/models/accident.py
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from .database import Base  # adapte selon ton import Base existant

class SeverityEnum(str, enum.Enum):
    minor   = "minor"    # léger
    serious = "serious"  # grave
    fatal   = "fatal"    # mortel
    unknown = "unknown"  # inconnu

class VehicleTypeEnum(str, enum.Enum):
    moto       = "moto"
    voiture    = "voiture"
    velo       = "velo"
    camion     = "camion"
    pietton    = "pieton"
    autre      = "autre"

class RoadTypeEnum(str, enum.Enum):
    carrefour    = "carrefour"
    virage       = "virage"
    ligne_droite = "ligne_droite"
    rondpoint    = "rondpoint"
    autre        = "autre"

class AccidentEvent(Base):
    __tablename__ = "accident_events"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Lié au profil utilisateur (optionnel si SOS anonyme)
    user_id        = Column(UUID(as_uuid=True), nullable=True)
    qr_token       = Column(String, nullable=True)

    # Position GPS — collectée automatiquement au SOS
    latitude       = Column(Float, nullable=False)
    longitude      = Column(Float, nullable=False)
    zone_name      = Column(String, nullable=True)   # ex: "Avenue de la Marina, Lomé"

    # Horodatage
    timestamp      = Column(DateTime(timezone=True), server_default=func.now())
    hour_of_day    = Column(Integer, nullable=True)  # 0-23 calculé auto
    day_of_week    = Column(Integer, nullable=True)  # 0=lundi, 6=dimanche

    # Données auto depuis l'app mobile
    vehicle_type   = Column(String, default="moto")

    # Données enrichies par le secouriste via dashboard Pro
    severity       = Column(String, default="unknown")
    road_type      = Column(String, nullable=True)
    weather        = Column(String, nullable=True)   # récupéré via API météo
    cause_probable = Column(String, nullable=True)   # ex: "excès de vitesse"

    # Calculé automatiquement
    is_hotspot     = Column(Boolean, default=False)

    # Statut de l'alerte
    resolved       = Column(Boolean, default=False)
    resolved_at    = Column(DateTime(timezone=True), nullable=True)