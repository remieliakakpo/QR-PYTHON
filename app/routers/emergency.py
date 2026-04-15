from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import get_db

router = APIRouter()

@router.get("/nearest")
async def get_nearest_hospital(lat: float, lon: float, db: Session = Depends(get_db)):
    # Requête SQL utilisant PostGIS pour trouver l'hôpital le plus proche
    # ST_Distance calcule la distance entre le point fourni et les hôpitaux en base
    query = text("""
        SELECT name, phone, latitude, longitude
        FROM medical_facilities
        ORDER BY location <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        LIMIT 1;
    """)
    
    result = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
    
    if result:
        return {
            "name": result.name,
            "phone": result.phone,
            "latitude": result.latitude,
            "longitude": result.longitude
        }
    
    # Fallback si aucun hôpital n'est en base
    return {
        "name": "Hôpital Dogta-Lafiè",
        "phone": "+22822530100",
        "latitude": 6.2085,
        "longitude": 1.2015
    }