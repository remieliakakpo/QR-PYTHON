import uuid
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
from pydantic import BaseModel

class AlerteEvent(Base):
    __tablename__ = "alerte_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255))
    qr_token = Column(String(255))
    prenom = Column(String(255), default="Inconnu")
    nom = Column(String(255), default="")
    groupe_sanguin = Column(String(10))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    adresse = Column(String(500), default="Position GPS")
    vehicle_type = Column(String(50), default="moto")
    statut = Column(String(50), default="active")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
class AccidentCreate(BaseModel):
    """Données envoyées automatiquement depuis l'app mobile au SOS"""
    latitude:     float
    longitude:    float
    user_id:      Optional[str] = None
    qr_token:     Optional[str] = None
    vehicle_type: Optional[str] = "moto"

class AccidentUpdate(BaseModel):
    """Données ajoutées par le secouriste depuis le dashboard Pro"""
    severity:       Optional[str] = None
    road_type:      Optional[str] = None
    cause_probable: Optional[str] = None
    resolved:       Optional[bool] = None

class AccidentResponse(BaseModel):
    id:             str
    latitude:       float
    longitude:      float
    zone_name:      Optional[str]
    timestamp:      datetime
    hour_of_day:    Optional[int]
    day_of_week:    Optional[int]
    vehicle_type:   Optional[str]
    severity:       Optional[str]
    road_type:      Optional[str]
    weather:        Optional[str]
    cause_probable: Optional[str]
    is_hotspot:     bool
    resolved:       bool

    class Config:
        from_attributes = True

class GeoJSONFeature(BaseModel):
    """Format GeoJSON standard pour Leaflet.js"""
    type: str = "Feature"
    geometry: dict
    properties: dict

class GeoJSONCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]

class HotspotZone(BaseModel):
    latitude:       float
    longitude:      float
    count:          int
    severity_score: float
    zone_name:      Optional[str]
    radius_meters:  int = 200