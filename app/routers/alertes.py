from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Float, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
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
# Garde en mémoire tous les dashboards connectés
# ════════════════════════════════════════════════════════════
class ConnectionManager:
    def __init__(self):
        # Liste de tous les dashboards Pro connectés
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Dashboard connecté. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Dashboard déconnecté. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Envoie un message à TOUS les dashboards connectés"""
        data = json.dumps(message, default=str)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)
        # Nettoyer les connexions mortes
        for conn in disconnected:
            self.active_connections.remove(conn)

# Instance globale — partagée entre tous les endpoints
manager = ConnectionManager()

# ════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════

# ─── WebSocket — le dashboard s'y connecte ───────────────────
@router.websocket("/ws/alertes")
async def websocket_alertes(websocket: WebSocket):
    """
    Le dashboard safelife-pro se connecte ici.
    Il reste connecté et reçoit les alertes en temps réel.
    """
    await manager.connect(websocket)
    try:
        # Garder la connexion ouverte indéfiniment
        while True:
            # On attend des messages du dashboard (ex: ping)
            data = await websocket.receive_text()
            # Répondre au ping pour garder la connexion vivante
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ─── POST /alertes — déclenché par l'app mobile au SOS ───────
@router.post("/alertes")
async def create_alerte(
    data: AlerteCreate,
    db: Session = Depends(get_db)
):
    """
    Appelé automatiquement depuis l'app mobile quand SOS est déclenché.
    1. Sauvegarde en base de données
    2. Broadcast WebSocket à tous les dashboards connectés
    """
    # 1. Sauvegarder l'alerte
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

    # 2. Broadcaster à tous les dashboards en temps réel
    message = {
        "type":           "NOUVELLE_ALERTE",  # ← le dashboard écoute ce type
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

# ─── GET /alertes — liste des alertes actives ────────────────
@router.get("/alertes")
def get_alertes(db: Session = Depends(get_db)):
    alertes = db.query(AlerteEvent).filter(
        AlerteEvent.statut != "resolue"
    ).order_by(AlerteEvent.timestamp.desc()).all()

    result = []
    for a in alertes:
        minutes = int((datetime.now() - a.timestamp.replace(tzinfo=None)).total_seconds() / 60)
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
    return {"alertes": result}

# ─── PUT /alertes/{id}/prendre-en-charge ─────────────────────
@router.put("/alertes/{alerte_id}/prendre-en-charge")
async def prendre_en_charge(
    alerte_id: str,
    db: Session = Depends(get_db)
):
    alerte = db.query(AlerteEvent).filter(
        AlerteEvent.id == alerte_id
    ).first()
    if not alerte:
        return {"error": "Alerte introuvable"}

    alerte.statut = "en_cours"
    db.commit()

    # Notifier tous les dashboards
    await manager.broadcast({
        "type":      "ALERTE_MISE_A_JOUR",
        "id":        alerte_id,
        "statut":    "en_cours",
    })
    return {"success": True}

# ─── PUT /alertes/{id}/resoudre ──────────────────────────────
@router.put("/alertes/{alerte_id}/resoudre")
async def resoudre_alerte(
    alerte_id: str,
    db: Session = Depends(get_db)
):
    alerte = db.query(AlerteEvent).filter(
        AlerteEvent.id == alerte_id
    ).first()
    if not alerte:
        return {"error": "Alerte introuvable"}

    alerte.statut    = "resolue"
    alerte.resolved_at = datetime.now()
    db.commit()

    await manager.broadcast({
        "type":   "ALERTE_RESOLUE",
        "id":     alerte_id,
        "statut": "resolue",
    })
    return {"success": True}