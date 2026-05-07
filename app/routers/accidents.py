# backend/app/routers/accidents.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from typing import Optional, List
from datetime import datetime, timedelta
import httpx
import math

from app.database import get_db
from ..models.accident import AccidentEvent
from ..schemas.accident import (
    AccidentCreate, AccidentUpdate,
    AccidentResponse, GeoJSONCollection, HotspotZone
)

router = APIRouter(prefix="/accidents", tags=["accidents"])

# ─── Fonction utilitaire : récupérer la météo ───────────────
async def get_weather(lat: float, lon: float) -> str:
    """Appelle Open-Meteo (gratuit, sans clé API)"""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current_weather=true"
        )
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            data = resp.json()
            code = data.get("current_weather", {}).get("weathercode", -1)
            # Codes WMO simplifiés
            if code == 0:    return "ensoleillé"
            elif code <= 3:  return "nuageux"
            elif code <= 67: return "pluie"
            elif code <= 77: return "neige"
            else:            return "orage"
    except Exception:
        return "inconnu"

# ─── Reverse geocoding (zone_name depuis lat/lng) ────────────
async def get_zone_name(lat: float, lon: float) -> str:
    """Nominatim OpenStreetMap — gratuit"""
    try:
        url = (
            f"https://nominatim.openstreetmap.org/reverse"
            f"?lat={lat}&lon={lon}&format=json&accept-language=fr"
        )
        headers = {"User-Agent": "SafeLife-App/1.0"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            data = resp.json()
            address = data.get("address", {})
            road    = address.get("road", "")
            suburb  = address.get("suburb", "")
            city    = address.get("city", "Lomé")
            return f"{road}, {suburb}, {city}".strip(", ")
    except Exception:
        return "Lomé, Togo"

# ─── Calculer si une zone est un hotspot ─────────────────────
def calculate_hotspot(db: Session, lat: float, lon: float, radius_km: float = 0.5) -> bool:
    """Un point est hotspot si dans un rayon de 500m il y a >= 3 accidents"""
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
    
    count = db.query(AccidentEvent).filter(
        AccidentEvent.latitude.between(lat - lat_delta, lat + lat_delta),
        AccidentEvent.longitude.between(lon - lon_delta, lon + lon_delta)
    ).count()
    
    return count >= 3

# ════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════

# ─── POST /accidents — créé automatiquement au SOS ──────────
@router.post("/", response_model=AccidentResponse)
async def create_accident(data: AccidentCreate, db: Session = Depends(get_db)):
    """
    Appelé automatiquement depuis l'app mobile quand un SOS est déclenché.
    Enrichit les données avec météo et zone_name automatiquement.
    """
    now = datetime.now()
    
    # Enrichissement automatique
    weather   = await get_weather(data.latitude, data.longitude)
    zone_name = await get_zone_name(data.latitude, data.longitude)
    is_hot    = calculate_hotspot(db, data.latitude, data.longitude)

    accident = AccidentEvent(
        user_id      = data.user_id,
        qr_token     = data.qr_token,
        latitude     = data.latitude,
        longitude    = data.longitude,
        zone_name    = zone_name,
        hour_of_day  = now.hour,
        day_of_week  = now.weekday(),
        vehicle_type = data.vehicle_type or "moto",
        weather      = weather,
        is_hotspot   = is_hot,
    )
    db.add(accident)
    db.commit()
    db.refresh(accident)
    return accident

# ─── GET /accidents/geojson — pour la carte Leaflet ─────────
@router.get("/geojson")
async def get_accidents_geojson(
    days:     Optional[int]  = Query(30, description="Derniers N jours"),
    severity: Optional[str]  = Query(None),
    vehicle:  Optional[str]  = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retourne tous les accidents en format GeoJSON.
    Leaflet.js consomme directement ce format.
    """
    query = db.query(AccidentEvent)
    
    if days:
        since = datetime.now() - timedelta(days=days)
        query = query.filter(AccidentEvent.timestamp >= since)
    if severity:
        query = query.filter(AccidentEvent.severity == severity)
    if vehicle:
        query = query.filter(AccidentEvent.vehicle_type == vehicle)

    accidents = query.all()

    features = []
    for a in accidents:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [a.longitude, a.latitude]  # GeoJSON = [lng, lat]
            },
            "properties": {
                "id":             str(a.id),
                "zone_name":      a.zone_name,
                "timestamp":      a.timestamp.isoformat() if a.timestamp else None,
                "hour_of_day":    a.hour_of_day,
                "day_of_week":    a.day_of_week,
                "vehicle_type":   a.vehicle_type,
                "severity":       a.severity,
                "road_type":      a.road_type,
                "weather":        a.weather,
                "cause_probable": a.cause_probable,
                "is_hotspot":     a.is_hotspot,
            }
        })

    return {"type": "FeatureCollection", "features": features}

# ─── GET /accidents/heatmap — données pour leaflet.heat ──────
@router.get("/heatmap")
async def get_heatmap_data(
    days: Optional[int] = Query(90),
    db: Session = Depends(get_db)
):
    """
    Format attendu par leaflet.heat : [[lat, lng, intensity], ...]
    intensity = 1.0 pour fatal, 0.6 pour grave, 0.3 pour léger
    """
    since = datetime.now() - timedelta(days=days)
    accidents = db.query(AccidentEvent).filter(
        AccidentEvent.timestamp >= since
    ).all()

    severity_weights = {
        "fatal":   1.0,
        "serious": 0.6,
        "minor":   0.3,
        "unknown": 0.2,
    }

    points = []
    for a in accidents:
        weight = severity_weights.get(a.severity or "unknown", 0.2)
        points.append([a.latitude, a.longitude, weight])

    return {"points": points, "total": len(points)}

# ─── GET /accidents/hotspots — zones à risque ────────────────
@router.get("/hotspots")
async def get_hotspots(db: Session = Depends(get_db)):
    """Retourne les zones avec >= 3 accidents dans un rayon de 500m"""
    hotspots = db.query(AccidentEvent).filter(
        AccidentEvent.is_hotspot == True
    ).all()

    # Grouper par zone_name pour éviter les doublons
    zones: dict = {}
    for a in hotspots:
        key = a.zone_name or f"{round(a.latitude,3)},{round(a.longitude,3)}"
        if key not in zones:
            zones[key] = {
                "latitude":   a.latitude,
                "longitude":  a.longitude,
                "zone_name":  a.zone_name,
                "count":      0,
                "fatal":      0,
                "serious":    0,
            }
        zones[key]["count"]   += 1
        if a.severity == "fatal":   zones[key]["fatal"]   += 1
        if a.severity == "serious": zones[key]["serious"] += 1

    result = []
    for zone_name, data in zones.items():
        score = (data["fatal"] * 3 + data["serious"] * 2 + data["count"]) / data["count"]
        result.append({**data, "severity_score": round(score, 2)})

    return sorted(result, key=lambda x: x["severity_score"], reverse=True)

# ─── GET /accidents/stats — analytics pour le dashboard ──────
@router.get("/stats")
async def get_stats(
    days: Optional[int] = Query(30),
    db: Session = Depends(get_db)
):
    """Statistiques complètes pour les graphiques du dashboard"""
    since = datetime.now() - timedelta(days=days)
    base  = db.query(AccidentEvent).filter(AccidentEvent.timestamp >= since)

    total = base.count()

    # Par heure de la journée
    by_hour = db.query(
        AccidentEvent.hour_of_day,
        func.count(AccidentEvent.id).label("count")
    ).filter(AccidentEvent.timestamp >= since).group_by(
        AccidentEvent.hour_of_day
    ).all()

    # Par type de véhicule
    by_vehicle = db.query(
        AccidentEvent.vehicle_type,
        func.count(AccidentEvent.id).label("count")
    ).filter(AccidentEvent.timestamp >= since).group_by(
        AccidentEvent.vehicle_type
    ).all()

    # Par gravité
    by_severity = db.query(
        AccidentEvent.severity,
        func.count(AccidentEvent.id).label("count")
    ).filter(AccidentEvent.timestamp >= since).group_by(
        AccidentEvent.severity
    ).all()

    # Par météo
    by_weather = db.query(
        AccidentEvent.weather,
        func.count(AccidentEvent.id).label("count")
    ).filter(AccidentEvent.timestamp >= since).group_by(
        AccidentEvent.weather
    ).all()

    return {
        "total":       total,
        "hotspots":    base.filter(AccidentEvent.is_hotspot == True).count(),
        "resolved":    base.filter(AccidentEvent.resolved == True).count(),
        "by_hour":     [{"hour": h, "count": c} for h, c in by_hour if h is not None],
        "by_vehicle":  [{"type": t, "count": c} for t, c in by_vehicle],
        "by_severity": [{"severity": s, "count": c} for s, c in by_severity],
        "by_weather":  [{"weather": w, "count": c} for w, c in by_weather],
    }

# ─── PUT /accidents/{id} — enrichissement par secouriste ─────
@router.put("/{accident_id}", response_model=AccidentResponse)
def update_accident(
    accident_id: str,
    data: AccidentUpdate,
    db: Session = Depends(get_db)
):
    """Le secouriste enrichit les données depuis le dashboard Pro"""
    accident = db.query(AccidentEvent).filter(
        AccidentEvent.id == accident_id
    ).first()
    
    if not accident:
        raise HTTPException(status_code=404, detail="Accident introuvable")
    
    if data.severity       is not None: accident.severity       = data.severity
    if data.road_type      is not None: accident.road_type      = data.road_type
    if data.cause_probable is not None: accident.cause_probable = data.cause_probable
    if data.resolved       is not None:
        accident.resolved    = data.resolved
        accident.resolved_at = datetime.now() if data.resolved else None
    
    db.commit()
    db.refresh(accident)
    return accident