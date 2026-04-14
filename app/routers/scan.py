from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
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
    # 1. Chercher le profil correspondant au jeton
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        return """<html><body style="text-align:center;padding:50px;"><h1>404 - Profil introuvable</h1></body></html>"""

    # 2. Enregistrer le Scan (Historique et Géolocalisation)
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

    # 3. Préparation des données pour l'affichage
    full_name = f"{profile.first_name} {profile.last_name}"
    contacts = profile.emergency_contacts
    
    # Liste des 10 codes autorisés
    valid_codes = [
        "COM-1010", "COM-2020", "COM-3030", "COM-4040", "COM-5050",
        "AMBU-112", "AMBU-911", "AMBU-777", "AMBU-888", "AMBU-000"
    ]

    # 4. Génération du HTML Responsive avec Verrouillage
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>Accès Sécurisé - {full_name}</title>
        <style>
            #emergency-content {{ display: none; }}
            .lock-bg {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }}
        </style>
    </head>
    <body class="bg-slate-900 font-sans transition-colors duration-500">
        
        <div id="lock-screen" class="fixed inset-0 z-50 flex items-center justify-center p-4 lock-bg">
            <div class="bg-white rounded-3xl p-8 w-full max-w-sm text-center shadow-2xl">
                <div class="text-5xl mb-4">🛡️</div>
                <h1 class="text-2xl font-black text-slate-800 mb-2">Accès Restreint</h1>
                <p class="text-slate-500 text-sm mb-6">Saisissez votre code d'accréditation <br><span class="font-bold text-red-500">(COM- ou AMBU-)</span></p>
                
                <input type="text" id="codeInput" placeholder="Ex: AMBU-112" 
                       class="w-full border-2 border-slate-100 rounded-xl p-4 mb-4 text-center font-bold text-lg focus:border-red-500 outline-none uppercase transition-all">
                
                <button onclick="checkCode()" 
                        class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-4 rounded-xl shadow-lg transition-all active:scale-95">
                    Déverrouiller
                </button>
                <p id="errorMsg" class="text-red-500 text-xs mt-3 hidden font-bold">⚠️ Code invalide. Veuillez réessayer.</p>
            </div>
        </div>

        <div id="emergency-content" class="max-w-md mx-auto bg-white min-h-screen shadow-2xl pb-10">
            
            <div class="bg-red-600 p-6 text-white text-center">
                <h1 class="text-3xl font-black uppercase tracking-tighter">Urgence Médicale</h1>
                <p class="text-sm font-medium opacity-80">Informations vitales - SaveMe</p>
            </div>

            <div class="p-6 text-center border-b border-gray-100">
                <div class="w-20 h-20 bg-red-100 text-red-600 rounded-full mx-auto mb-3 flex items-center justify-center text-3xl font-bold border-2 border-red-200">
                    {profile.first_name[0]}{profile.last_name[0]}
                </div>
                <h2 class="text-2xl font-extrabold text-slate-800">{full_name}</h2>
                <p class="text-slate-400 text-sm font-bold uppercase tracking-widest">{profile.nationality}</p>
            </div>

            <div class="px-6 grid grid-cols-2 gap-3 -mt-4">
                <div class="bg-white border-2 border-red-500 p-4 rounded-2xl shadow-sm text-center">
                    <p class="text-[10px] text-red-500 uppercase font-black">Groupe Sanguin</p>
                    <p class="text-3xl font-black text-red-600">{profile.blood_type or '??'}</p>
                </div>
                <div class="bg-white border-2 border-slate-800 p-4 rounded-2xl shadow-sm text-center">
                    <p class="text-[10px] text-slate-400 uppercase font-black">Genre</p>
                    <p class="text-xl font-bold text-slate-800">{profile.gender}</p>
                </div>
            </div>

            <div class="p-6 space-y-4">
                <div class="bg-amber-50 p-4 rounded-xl border-l-4 border-amber-500">
                    <p class="text-xs font-black text-amber-600 uppercase mb-1">⚠️ Allergies & Intolérances</p>
                    <p class="text-slate-700 font-medium">{profile.allergies or 'Aucune connue'}</p>
                </div>

                <div class="bg-blue-50 p-4 rounded-xl border-l-4 border-blue-500">
                    <p class="text-xs font-black text-blue-600 uppercase mb-1">🩺 Pathologies / Antécédents</p>
                    <p class="text-slate-700 font-medium">{profile.conditions or 'Néant'}</p>
                </div>

                {f'''
                <div class="bg-slate-50 p-4 rounded-xl border-l-4 border-slate-500">
                    <p class="text-xs font-black text-slate-600 uppercase mb-1">♿ Handicap / Mobilité</p>
                    <p class="text-slate-700 font-medium">{profile.disabilities}</p>
                </div>
                ''' if profile.disabilities else ''}
            </div>

            <div class="px-6 mb-6">
                <h3 class="text-sm font-black text-slate-400 uppercase mb-4 tracking-widest">Contacts à prévenir</h3>
                <div class="space-y-3">
                    {" ".join([f'''
                    <a href="tel:{c.phone}" class="flex items-center justify-between bg-emerald-500 hover:bg-emerald-600 text-white p-4 rounded-2xl transition-transform active:scale-95 shadow-md">
                        <div>
                            <p class="text-[10px] font-black uppercase opacity-70">{c.relation}</p>
                            <p class="text-lg font-bold">{c.name}</p>
                        </div>
                        <div class="bg-white/20 p-2 rounded-full font-bold text-sm">📞 Appeler</div>
                    </a>
                    ''' for c in contacts])}
                </div>
            </div>

            {f'''
            <div class="mx-6 p-4 bg-slate-800 rounded-2xl text-white">
                <p class="text-[10px] font-black uppercase opacity-50 mb-2">Identification Véhicule</p>
                <div class="flex justify-between items-center">
                    <span class="font-bold">{profile.brand} {profile.model}</span>
                    <span class="bg-white text-slate-800 px-3 py-1 rounded-lg font-mono font-black">{profile.plate}</span>
                </div>
            </div>
            ''' if profile.has_vehicle else ''}

            <div class="mt-10 text-center px-6">
                <p class="text-[10px] text-slate-400">Ce profil est sécurisé par <strong>SaveMe</strong>. <br> Les données de localisation du scan ont été transmises.</p>
            </div>
        </div>

        <script>
            const validCodes = {valid_codes};

            function checkCode() {{
                const input = document.getElementById('codeInput');
                const code = input.value.trim().toUpperCase();
                const errorMsg = document.getElementById('errorMsg');

                if (validCodes.includes(code)) {{
                    document.getElementById('lock-screen').classList.add('hidden');
                    document.body.classList.replace('bg-slate-900', 'bg-slate-100');
                    document.getElementById('emergency-content').style.display = 'block';
                }} else {{
                    errorMsg.classList.remove('hidden');
                    input.classList.add('border-red-500');
                    input.value = '';
                }}
            }}

            document.getElementById('codeInput').addEventListener('keypress', function (e) {{
                if (e.key === 'Enter') checkCode();
            }});
        </script>
    </body>
    </html>
    """
    return html_content