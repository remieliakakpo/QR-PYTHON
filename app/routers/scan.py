from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import get_db
from app.models.models import Scan, Profile
from pydantic import BaseModel
import uuid

router = APIRouter()

# --- SCHEMA POUR L'APP MOBILE ---
class MobileScanRequest(BaseModel):
    token: str
    pin: str
    authority_type: str

# --- 1. ROUTE POUR L'APPLICATION MOBILE (RETOUR JSON) ---
@router.post("/verify")
def verify_mobile_scan(request: MobileScanRequest, db: Session = Depends(get_db)):
    # Nettoyage du code saisi
    clean_pin = request.pin.strip().upper()
    
    # Codes Maîtres Universels
    MASTER_CODES = ["POL1717", "AMBU1818"]

    # Recherche du profil via le qr_token
    profile = db.query(Profile).filter(Profile.qr_token == request.token).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # Vérification : Code Maître ou Code Personnel
    user_code = str(getattr(profile, 'access_code', '1234')).upper()
    
    if clean_pin in MASTER_CODES or clean_pin == user_code:
        return {
            "identity": {
                "first_name": profile.first_name,
                "last_name": profile.last_name
            },
            "medical": {
                "blood_type": profile.blood_type or "NC",
                "handicaps": getattr(profile, 'handicaps', 'AUCUN') # Affiche uniquement les handicaps
            },
            "emergency_contact": f"{profile.emergency_contacts[0].phone}" if profile.emergency_contacts else "N/A",
            "audit": {
                "status": "DÉVERROUILLÉ",
                "authority": request.authority_type
            }
        }

    raise HTTPException(status_code=403, detail="Code invalide pour cette unité")


# --- 2. ROUTE POUR LE NAVIGATEUR (RETOUR HTML) ---
@router.get("/{qr_token}", response_class=HTMLResponse)
def log_and_display_profile(
    qr_token: str,
    request: Request,
    db: Session = Depends(get_db),
    lat: float = None,
    lon: float = None,
):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    
    if not profile:
        return HTMLResponse(content="<h1>404 - Profil introuvable</h1>", status_code=404)

    # Enregistrement du Scan
    new_scan = Scan(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        latitude=lat,
        longitude=lon,
        scanner_ip=request.client.host,
        alert_sent=False,
    )
    db.add(new_scan)
    db.commit()

    # Liste des codes valides pour le JavaScript du navigateur
    valid_codes = ["POL1717", "AMBU1818"] 
    user_code = str(getattr(profile, 'access_code', '1234')).upper()
    valid_codes.append(user_code)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>Urgence SafeLife</title>
        <style>
            #emergency-content {{ display: none; }}
            .lock-bg {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }}
        </style>
    </head>
    <body class="bg-slate-900 transition-colors duration-500">
        
        <div id="lock-screen" class="fixed inset-0 z-50 flex items-center justify-center p-4 lock-bg">
            <div class="bg-white rounded-3xl p-8 w-full max-w-sm text-center shadow-2xl">
                <div class="text-5xl mb-4">🛡️</div>
                <h1 class="text-2xl font-black text-slate-800 mb-2">Accès Restreint</h1>
                <input type="text" id="codeInput" placeholder="CODE ACCÈS" 
                       class="w-full border-2 border-slate-100 rounded-xl p-4 mb-4 text-center font-bold text-lg outline-none uppercase">
                <button onclick="checkCode()" class="w-full bg-red-600 text-white font-bold py-4 rounded-xl">DÉVERROUILLER</button>
                <p id="errorMsg" class="text-red-500 text-xs mt-3 hidden font-bold">⚠️ Code invalide pour cette unité.</p>
            </div>
        </div>

        <div id="emergency-content" class="max-w-md mx-auto bg-white min-h-screen">
            <div class="bg-red-600 p-6 text-white text-center">
                <h1 class="text-2xl font-black italic underline decoration-white">SAFEME TOGO</h1>
            </div>
            
            <div class="p-8 text-center">
                <div class="w-20 h-20 bg-slate-800 text-white rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold">
                    {profile.first_name[0]}{profile.last_name[0]}
                </div>
                <h2 class="text-2xl font-black text-slate-900 uppercase">{profile.first_name} {profile.last_name}</h2>
            </div>

            <div class="px-6 grid grid-cols-1 gap-4">
                <div class="bg-red-50 border-2 border-red-600 p-6 rounded-3xl text-center">
                    <p class="text-xs text-red-600 font-black uppercase">Groupe Sanguin</p>
                    <p class="text-5xl font-black text-red-600">{profile.blood_type or '??'}</p>
                </div>

                <div class="bg-slate-50 border-2 border-slate-800 p-6 rounded-3xl">
                    <p class="text-xs text-slate-500 font-black uppercase mb-2">♿ Handicaps / Restrictions</p>
                    <p class="text-lg font-bold text-slate-800 uppercase">{getattr(profile, 'handicaps', 'AUCUN HANDICAP DÉCLARÉ')}</p>
                </div>
            </div>

            <div class="p-6 mt-4">
                <h3 class="text-xs font-black text-slate-400 uppercase mb-4 tracking-widest text-center">Contact d'urgence</h3>
                {" ".join([f'''
                <a href="tel:{c.phone}" class="flex items-center justify-between bg-emerald-600 text-white p-5 rounded-2xl shadow-lg">
                    <p class="font-extrabold">{c.name}</p>
                    <div class="bg-white/20 px-3 py-1 rounded text-xs">APPELER</div>
                </a>
                ''' for c in profile.emergency_contacts])}
            </div>
        </div>

        <script>
            const validCodes = {valid_codes};
            function checkCode() {{
                const input = document.getElementById('codeInput');
                const code = input.value.trim().toUpperCase();
                if (validCodes.includes(code)) {{
                    document.getElementById('lock-screen').style.display = 'none';
                    document.getElementById('emergency-content').style.display = 'block';
                }} else {{
                    document.getElementById('errorMsg').classList.remove('hidden');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)