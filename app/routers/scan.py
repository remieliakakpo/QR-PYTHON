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

    # 4. Génération du HTML Responsive (Tailwind CSS)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>URGENCE - {full_name}</title>
    </head>
    <body class="bg-slate-100 font-sans">
        <div class="max-w-md mx-auto bg-white min-h-screen shadow-2xl pb-10">
            
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
                        <div class="bg-white/20 p-2 rounded-full font-bold">📞 Appeler</div>
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
    </body>
    </html>
    """
    return html_content