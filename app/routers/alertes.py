from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Float, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import json
import enum

from ..database import Base, get_db

router = APIRouter()

# ─── Modèle base de données ──────────────────────────────────
class StatutAlerte(str, enum.Enum):
    active   = "active"
    en_cours = "en_cours"
    resolue  = "resolue"

class AlerteEvent(Base):
    __tablename__ = "alerte_events"
    # CORRECTIF RAILWAY : Évite l'erreur "Table already defined" au redémarrage
    __table_args__ = {'extend_existing': True} 

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(String, nullable=True)
    qr_token       = Column(String, nullable=True)
    prenom         = Column(String, nullable=True)
    nom            = Column(String, nullable=True)
    groupe_sanguin = Column(String, nullable=True)
    electrophorese = Column(String, nullable=True)
    latitude       = Column(Float, nullable=False)
    longitude      = Column(Float, nullable=False)
    adresse        = Column(String, nullable=True)
    vehicle_type   = Column(String, nullable=True)
    statut         = Column(String, default="active")
    timestamp      = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at    = Column(DateTime(timezone=True), nullable=True)

# ─── Schémas ────────────────────────────────────────────────
class AlerteCreate(BaseModel):
    user_id:        Optional[str] = None
    qr_token:       Optional[str] = None
    prenom:         Optional[str] = None
    nom:            Optional[str] = None
    groupe_sanguin: Optional[str] = None
    electrophorese: Optional[str] = None
    latitude:       float
    longitude:      float
    adresse:        Optional[str] = None
    vehicle_type:   Optional[str] = "moto"

class AlerteUpdate(BaseModel):
    statut: str  # "en_cours" | "resolue"

# ════════════════════════════════════════════════════════════
# GESTIONNAIRE WEBSOCKET
# ════════════════════════════════════════════════════════════
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Dashboard connecté. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"❌ Dashboard déconnecté. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# ════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════

@router.websocket("/ws/alertes")
async def websocket_alertes(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/alertes")
async def create_alerte(data: AlerteCreate, db: Session = Depends(get_db)):
    alerte = AlerteEvent(
        user_id        = data.user_id,
        qr_token       = data.qr_token,
        prenom         = data.prenom or "Inconnu",
        nom            = data.nom or "",
        groupe_sanguin = data.groupe_sanguin or "?",
        electrophorese = data.electrophorese,
        latitude       = data.latitude,
        longitude      = data.longitude,
        adresse        = data.adresse or "Position GPS",
        vehicle_type   = data.vehicle_type or "moto",
        statut         = "active",
    )
    db.add(alerte)
    db.commit()
    db.refresh(alerte)

    message = {
        "type":           "NOUVELLE_ALERTE",
        "id":             str(alerte.id),
        "prenom":         alerte.prenom,
        "nom":            alerte.nom,
        "groupe_sanguin": alerte.groupe_sanguin,
        "electrophorese": alerte.electrophorese,
        "latitude":       alerte.latitude,
        "longitude":      alerte.longitude,
        "adresse":        alerte.adresse,
        "vehicle_type":   alerte.vehicle_type,
        "statut":         alerte.statut,
        "timestamp":      alerte.timestamp.isoformat(),
        "minutes_ecoulees": 0,
        "contacts":       [],
    }
    await manager.broadcast(message)
    return {"success": True, "alerte_id": str(alerte.id)}

@router.get("/alertes")
def get_alertes(db: Session = Depends(get_db)):
    alertes = db.query(AlerteEvent).filter(
        AlerteEvent.statut != "resolue"
    ).order_by(AlerteEvent.timestamp.desc()).all()

    result = []
    now = datetime.now(timezone.utc)
    for a in alertes:
        # Calcul propre du temps écoulé
        diff = now - a.timestamp.replace(tzinfo=timezone.utc) if a.timestamp.tzinfo else now - a.timestamp
        minutes = int(diff.total_seconds() / 60)
        result.append({
            "id":             str(a.id),
            "prenom":         a.prenom,
            "nom":            a.nom,
            "groupe_sanguin": a.groupe_sanguin,
            "electrophorese": a.electrophorese,
            "latitude":       a.latitude,
            "longitude":      a.longitude,
            "adresse":        a.adresse,
            "vehicle_type":   a.vehicle_type,
            "statut":         a.statut,
            "timestamp":      a.timestamp.isoformat(),
            "minutes_ecoulees": max(0, minutes),
            "contacts":       [],
        })
    return result # Retourne directement la liste pour matcher avec ton frontend

@router.put("/alertes/{alerte_id}/prendre-en-charge")
async def prendre_en_charge(alerte_id: str, db: Session = Depends(get_db)):
    alerte = db.query(AlerteEvent).filter(AlerteEvent.id == alerte_id).first()
    if not alerte: return {"error": "Alerte introuvable"}
    alerte.statut = "en_cours"
    db.commit()
    await manager.broadcast({"type": "ALERTE_MISE_A_JOUR", "id": alerte_id, "statut": "en_cours"})
    return {"success": True}

@router.put("/alertes/{alerte_id}/resoudre")
async def resoudre_alerte(alerte_id: str, db: Session = Depends(get_db)):
    alerte = db.query(AlerteEvent).filter(AlerteEvent.id == alerte_id).first()
    if not alerte: return {"error": "Alerte introuvable"}
    alerte.statut = "resolue"
    alerte.resolved_at = datetime.now(timezone.utc)
    db.commit()
    await manager.broadcast({"type": "ALERTE_RESOLUE", "id": alerte_id, "statut": "resolue"})
    return {"success": True}