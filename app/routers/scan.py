from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import get_db
from app.models.models import Scan, Profile
import uuid

router = APIRouter()

@router.get("/{qr_token}", response_class=HTMLResponse)
def log_and_display_profile(
    qr_token: str,
    request: Request,
    db: Session = Depends(get_db),
    lat: float = None,
    lon: float = None,
):
    # 1. Recherche du profil via le token unique du QR Code
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    
    if not profile:
        return HTMLResponse(
            content="""<html><body style="text-align:center;padding:50px;font-family:sans-serif;">
                       <h1>404 - Profil introuvable</h1>
                       <p>Ce code QR ne semble pas correspondre à un utilisateur SafeLife.</p>
                       </body></html>""", 
            status_code=404
        )

    # 2. Identification de l'hôpital le plus proche (Logique PostGIS)
    nearest_hospital = "Localisation en cours..."
    if lat and lon:
        try:
            query = text("""
                SELECT name FROM medical_facilities 
                ORDER BY location <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) 
                LIMIT 1;
            """)
            hospital_res = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
            if hospital_res:
                nearest_hospital = hospital_res.name
        except Exception:
            nearest_hospital = "Service de géolocalisation indisponible"

    # 3. Enregistrement du Scan dans la base de données
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

    # 4. Préparation des données pour le HTML
    full_name = f"{profile.first_name} {profile.last_name}"
    
    # Liste des codes d'accès (Services de secours + Code perso)
    valid_codes = [
        "COM-1010", "COM-2020", "COM-3030", "COM-4040", "COM-5050",
        "AMBU-112", "AMBU-911", "AMBU-777", "AMBU-888", "AMBU-000"
    ]
    # On récupère le code personnel de l'utilisateur (par défaut 1234 si vide)
    user_code = str(getattr(profile, 'access_code', '1234')).upper()
    valid_codes.append(user_code)

    # 5. Construction du Template HTML (Tailwind CSS)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>Urgence - {full_name}</title>
        <style>
            #emergency-content {{ display: none; }}
            .lock-bg {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }}
            .blood-glow {{ box-shadow: 0 0 15px rgba(220, 38, 38, 0.5); }}
        </style>
    </head>
    <body class="bg-slate-900 font-sans transition-colors duration-500">
        
        <div id="lock-screen" class="fixed inset-0 z-50 flex items-center justify-center p-4 lock-bg">
            <div class="bg-white rounded-3xl p-8 w-full max-w-sm text-center shadow-2xl">
                <div class="text-5xl mb-4">🛡️</div>
                <h1 class="text-2xl font-black text-slate-800 mb-2">Accès Restreint</h1>
                <p class="text-slate-500 text-sm mb-6">Saisissez le code d'accréditation <br>
                <span class="font-bold text-red-500">(Services de Secours ou Proches)</span></p>
                
                <input type="text" id="codeInput" placeholder="CODE ACCÈS" 
                       class="w-full border-2 border-slate-100 rounded-xl p-4 mb-4 text-center font-bold text-lg focus:border-red-500 outline-none uppercase transition-all">
                
                <button onclick="checkCode()" 
                        class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-4 rounded-xl shadow-lg transition-all active:scale-95">
                    DÉVERROUILLER
                </button>
                <p id="errorMsg" class="text-red-500 text-xs mt-3 hidden font-bold">⚠️ Accès refusé.</p>
            </div>
        </div>

        <div id="emergency-content" class="max-w-md mx-auto bg-slate-50 min-h-screen shadow-2xl pb-10">
            <div class="bg-red-600 p-6 text-white text-center shadow-lg">
                <h1 class="text-3xl font-black uppercase tracking-tighter italic">SAFELIFE</h1>
                <p class="text-xs font-bold opacity-90 tracking-widest">INFORMATIONS D'URGENCE</p>
            </div>

            <div class="p-6 text-center border-b border-gray-200 bg-white">
                <div class="w-20 h-20 bg-red-600 text-white rounded-full mx-auto mb-3 flex items-center justify-center text-3xl font-black border-4 border-white shadow-lg">
                    {profile.first_name[0]}{profile.last_name[0]}
                </div>
                <h2 class="text-2xl font-extrabold text-slate-900">{full_name}</h2>
                <div class="flex items-center justify-center gap-2 mt-1">
                    <span class="bg-slate-800 text-white text-[10px] px-2 py-1 rounded font-bold uppercase">{profile.nationality or 'TOGO'}</span>
                    <span class="text-slate-400 font-bold text-xs italic">📍 {nearest_hospital}</span>
                </div>
            </div>

            <div class="px-6 grid grid-cols-2 gap-3 -mt-4">
                <div class="bg-white border-2 border-red-600 p-4 rounded-2xl shadow-md text-center blood-glow">
                    <p class="text-[10px] text-red-600 uppercase font-black">Groupe Sanguin</p>
                    <p class="text-4xl font-black text-red-600">{profile.blood_type or '??'}</p>
                </div>
                <div class="bg-white border-2 border-slate-800 p-4 rounded-2xl shadow-md text-center">
                    <p class="text-[10px] text-slate-500 uppercase font-black">Genre</p>
                    <p class="text-xl font-bold text-slate-800">{profile.gender or 'N/A'}</p>
                </div>
            </div>

            <div class="p-6 space-y-4">
                <div class="bg-amber-50 p-4 rounded-xl border-l-8 border-amber-500 shadow-sm">
                    <p class="text-xs font-black text-amber-600 uppercase mb-1">⚠️ Allergies & Intolérances</p>
                    <p class="text-slate-800 font-bold">{profile.allergies or 'AUCUNE CONNUE'}</p>
                </div>
                <div class="bg-blue-50 p-4 rounded-xl border-l-8 border-blue-600 shadow-sm">
                    <p class="text-xs font-black text-blue-600 uppercase mb-1">🩺 Antécédents / Pathologies</p>
                    <p class="text-slate-800 font-bold">{profile.conditions or 'NÉANT'}</p>
                </div>
            </div>

            <div class="px-6 mb-6">
                <h3 class="text-xs font-black text-slate-400 uppercase mb-4 tracking-widest pl-1">Personnes à prévenir</h3>
                <div class="space-y-3">
                    {" ".join([f'''
                    <a href="tel:{c.phone}" class="flex items-center justify-between bg-emerald-600 text-white p-4 rounded-2xl shadow-lg active:scale-95 transition-transform">
                        <div>
                            <p class="text-[10px] font-black uppercase opacity-80">{c.relation or 'Urgence'}</p>
                            <p class="text-lg font-extrabold">{c.name}</p>
                        </div>
                        <div class="bg-white/20 px-4 py-2 rounded-full font-black text-xs uppercase tracking-tighter">Appeler</div>
                    </a>
                    ''' for c in profile.emergency_contacts])}
                </div>
            </div>

            <div class="mt-8 text-center px-6 border-t pt-6 border-slate-200">
                <p class="text-[9px] text-slate-400 font-black uppercase tracking-[0.2em]">Sécurisé par le protocole SafeMe Togo</p>
            </div>
        </div>

        <script>
            const validCodes = {valid_codes};

            function checkCode() {{
                const input = document.getElementById('codeInput');
                const code = input.value.trim().toUpperCase();
                const errorMsg = document.getElementById('errorMsg');

                if (validCodes.includes(code)) {{
                    document.getElementById('lock-screen').style.opacity = '0';
                    setTimeout(() => {{
                        document.getElementById('lock-screen').style.display = 'none';
                        document.body.classList.replace('bg-slate-900', 'bg-slate-100');
                        document.getElementById('emergency-content').style.display = 'block';
                    }}, 300);
                }} else {{
                    errorMsg.classList.remove('hidden');
                    input.classList.add('border-red-500');
                    input.value = '';
                    // Vibration légère si mobile
                    if (window.navigator.vibrate) window.navigator.vibrate(100);
                }}
            }}

            document.getElementById('codeInput').addEventListener('keypress', function (e) {{
                if (e.key === 'Enter') checkCode();
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)