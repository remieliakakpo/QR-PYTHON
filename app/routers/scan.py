from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
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

# --- 1. ROUTE POUR L'APPLICATION MOBILE (JSON) ---
# Cette route est appelée par l'app après le scan du QR Code
@router.post("/verify")
def verify_mobile_scan(request: MobileScanRequest, db: Session = Depends(get_db)):
    # Nettoyage du PIN (Majuscules et suppression d'espaces)
    clean_pin = str(request.pin).strip().upper()
    
    # Codes Maîtres Universels (Police & Ambulance)
    MASTER_CODES = ["POL1717", "AMBU1818"]

    # RECHERCHE : On accepte le QR_TOKEN ou l'ID direct
    profile = db.query(Profile).filter(
        (Profile.qr_token == request.token) | (Profile.id == request.token)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # Récupération du code personnel de la victime
    db_pin = getattr(profile, 'access_code', None) or "1234"
    user_code = str(db_pin).strip().upper()

    # LOGIQUE DE DÉVERROUILLAGE
    if clean_pin in MASTER_CODES or clean_pin == user_code:
        # Retour JSON "plat" pour un affichage direct sur le mobile
        return {
            "status": "DÉVERROUILLÉ",
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "blood_type": profile.blood_type or "NC",
            "allergies": getattr(profile, 'allergies', 'AUCUNE'),
            "conditions": getattr(profile, 'conditions', 'AUCUNE'),
            "medications": getattr(profile, 'medications', 'AUCUN'),
            "handicaps": getattr(profile, 'handicaps', 'AUCUN'),
            "emergency_contact_name": profile.emergency_contacts[0].name if profile.emergency_contacts else "Contact d'urgence",
            "emergency_contact_phone": profile.emergency_contacts[0].phone if profile.emergency_contacts else "N/A",
            "audit": {
                "authority": request.authority_type,
                "method": "MASTER_CODE" if clean_pin in MASTER_CODES else "USER_PIN"
            }
        }

    raise HTTPException(status_code=403, detail="Code d'accès invalide")

# --- 2. ROUTE POUR LE NAVIGATEUR (HTML) ---
# Cette route affiche la page de secours si quelqu'un scanne avec un téléphone classique
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

    # Enregistrement du scan dans l'historique (Audit GRC)
    try:
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
    except Exception as e:
        print(f"Erreur audit scan: {e}")

    # Préparation des codes autorisés pour le script JS de la page
    db_pin = getattr(profile, 'access_code', None) or "1234"
    valid_codes = ["POL1717", "AMBU1818", str(db_pin).strip().upper()]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>Urgence SafeMe</title>
        <style>
            #emergency-content {{ display: none; }}
            .lock-bg {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }}
        </style>
    </head>
    <body class="bg-slate-900">
        <div id="lock-screen" class="fixed inset-0 z-50 flex items-center justify-center p-4 lock-bg">
            <div class="bg-white rounded-3xl p-8 w-full max-w-sm text-center shadow-2xl">
                <div class="text-5xl mb-4">🛡️</div>
                <h1 class="text-2xl font-black text-slate-800 mb-2">Accès Restreint</h1>
                <p class="text-slate-500 mb-6 text-sm">Entrez le code d'unité (Police/Ambulance) ou le code de la victime.</p>
                <input type="text" id="codeInput" placeholder="CODE" 
                       class="w-full border-2 border-slate-100 rounded-xl p-4 mb-4 text-center font-bold text-2xl outline-none uppercase">
                <button onclick="checkCode()" class="w-full bg-red-600 text-white font-bold py-4 rounded-xl text-lg hover:bg-red-700 transition">DÉVERROUILLER</button>
                <p id="errorMsg" class="text-red-500 text-xs mt-3 hidden font-bold italic">⚠️ Code incorrect.</p>
            </div>
        </div>

        <div id="emergency-content" class="max-w-md mx-auto bg-white min-h-screen pb-10">
            <div class="bg-red-600 p-6 text-white text-center shadow-lg">
                <h1 class="text-2xl font-black italic underline tracking-tighter">SAFEME TOGO</h1>
            </div>
            
            <div class="p-8 text-center">
                <div class="w-24 h-24 bg-slate-800 text-white rounded-full mx-auto mb-4 flex items-center justify-center text-4xl font-black shadow-xl">
                    {profile.first_name[0]}{profile.last_name[0]}
                </div>
                <h2 class="text-3xl font-black text-slate-900 uppercase tracking-tight">{profile.first_name} {profile.last_name}</h2>
            </div>

            <div class="px-6 space-y-4">
                <div class="bg-red-50 border-l-8 border-red-600 p-6 rounded-2xl">
                    <p class="text-xs text-red-600 font-black uppercase tracking-widest">Groupe Sanguin</p>
                    <p class="text-6xl font-black text-red-600 mt-1">{profile.blood_type or 'NC'}</p>
                </div>

                <div class="bg-slate-50 border-l-8 border-slate-800 p-6 rounded-2xl">
                    <p class="text-xs text-slate-500 font-black uppercase tracking-widest mb-2">♿ Pathologies / Handicaps</p>
                    <p class="text-xl font-bold text-slate-800 uppercase leading-tight">{getattr(profile, 'conditions', 'AUCUNE')}</p>
                </div>
                
                <div class="bg-amber-50 border-l-8 border-amber-500 p-6 rounded-2xl">
                    <p class="text-xs text-amber-600 font-black uppercase tracking-widest mb-2">⚠️ Allergies</p>
                    <p class="text-xl font-bold text-amber-700 uppercase leading-tight">{getattr(profile, 'allergies', 'AUCUNE')}</p>
                </div>
            </div>

            <div class="p-6 mt-6">
                <h3 class="text-xs font-black text-slate-400 uppercase mb-4 tracking-widest text-center italic">En cas d'urgence, appeler :</h3>
                {" ".join([f'''
                <a href="tel:{c.phone}" class="flex items-center justify-between bg-emerald-600 text-white p-5 rounded-2xl shadow-xl hover:bg-emerald-700 transition mb-3">
                    <div class="flex items-center gap-3">
                        <span class="text-2xl">📞</span>
                        <p class="font-black text-lg">{c.name}</p>
                    </div>
                    <div class="bg-white/20 px-3 py-1 rounded-lg text-xs font-bold">ICE</div>
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
                    input.value = '';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)