from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.models import Scan, Profile
from pydantic import BaseModel
import uuid

router = APIRouter()

class ScanVerifyRequest(BaseModel):
    token: str
    pin: str
    authority_type: str = "emergency_unit"

MASTER_CODES = {
    "POL1717": "Police",
    "AMBU1818": "Ambulancier",
    "POMP2626": "Pompiers",
    "MEDC3737": "Médecin",
}

# ─── GET /scan/{qr_token} ── Fiche publique niveau 1
@router.get("/{qr_token}", response_class=HTMLResponse)
def public_profile(qr_token: str, request: Request, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil SafeLife introuvable")

    # Enregistrer le scan
    scan = Scan(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        scanner_ip=request.client.host if request.client else None,
        alert_sent=False,
    )
    db.add(scan)
    db.commit()

    # Contacts d'urgence
    contacts_html = ""
    for c in profile.emergency_contacts:
        contacts_html += f"""
        <div class="contact-card">
            <div class="contact-info">
                <span class="contact-name">{c.name}</span>
                <span class="contact-relation">{c.relation or 'Contact'}</span>
            </div>
            <a href="tel:{c.phone}" class="call-btn">📞 {c.phone}</a>
        </div>"""

    vehicle_html = ""
    if profile.has_vehicle:
        vehicle_html = f"""
        <div class="section">
            <h3>🚗 Véhicule</h3>
            <div class="info-row"><span>Type</span><strong>{profile.vehicle_type or 'N/A'}</strong></div>
            <div class="info-row"><span>Immatriculation</span><strong>{profile.plate or 'N/A'}</strong></div>
            <div class="info-row"><span>Marque / Modèle</span><strong>{(profile.brand or '') + ' ' + (profile.model or '')}</strong></div>
        </div>"""

    school_html = ""
    if profile.profile_type == "student" and profile.school_name:
        school_html = f"""
        <div class="section">
            <h3>🏫 École</h3>
            <div class="info-row"><span>École</span><strong>{profile.school_name}</strong></div>
            <div class="info-row"><span>Classe</span><strong>{profile.class_name or 'N/A'}</strong></div>
            <div class="info-row"><span>Directeur</span><strong>{profile.director_name or 'N/A'} — {profile.director_phone or 'N/A'}</strong></div>
            <div class="info-row"><span>Parent</span><strong>{profile.parent_name or 'N/A'} — {profile.parent_phone or 'N/A'}</strong></div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeLife — Fiche d'urgence</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f1f5f9; color: #1e293b; }}
        .header {{ background: linear-gradient(135deg, #007A3D, #005C2E); padding: 24px 20px; text-align: center; }}
        .logo {{ font-size: 28px; font-weight: 900; color: white; letter-spacing: 1px; }}
        .logo span {{ color: #FFCD00; }}
        .badge {{ background: rgba(255,255,255,0.15); color: white; padding: 4px 12px; border-radius: 99px; font-size: 12px; margin-top: 8px; display: inline-block; }}
        .container {{ max-width: 480px; margin: 0 auto; padding: 16px; }}
        .alert-banner {{ background: #fee2e2; border: 1px solid #fca5a5; border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; text-align: center; }}
        .alert-banner p {{ color: #dc2626; font-weight: 700; font-size: 14px; }}
        .section {{ background: white; border-radius: 16px; padding: 18px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
        .section h3 {{ font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 14px; }}
        .name {{ font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }}
        .profile-type {{ font-size: 13px; color: #64748b; }}
        .blood-badge {{ background: #fff1f2; border: 2px solid #fca5a5; border-radius: 12px; padding: 12px 20px; display: inline-flex; flex-direction: column; align-items: center; margin-bottom: 14px; }}
        .blood-label {{ font-size: 10px; color: #e11d48; font-weight: 800; text-transform: uppercase; }}
        .blood-value {{ font-size: 36px; font-weight: 900; color: #e11d48; line-height: 1.1; }}
        .info-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        .info-row:last-child {{ border-bottom: none; }}
        .info-row span {{ color: #64748b; }}
        .info-row strong {{ color: #0f172a; text-align: right; max-width: 60%; }}
        .contact-card {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; }}
        .contact-card:last-child {{ border-bottom: none; }}
        .contact-name {{ font-weight: 700; font-size: 15px; display: block; }}
        .contact-relation {{ font-size: 12px; color: #64748b; }}
        .call-btn {{ background: #007A3D; color: white; padding: 8px 14px; border-radius: 10px; font-size: 13px; font-weight: 700; text-decoration: none; white-space: nowrap; }}
        .pro-section {{ background: #0f172a; border-radius: 16px; padding: 18px; margin-bottom: 12px; }}
        .pro-section h3 {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; margin-bottom: 12px; }}
        .pro-input {{ width: 100%; background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 14px; color: white; font-size: 20px; text-align: center; font-weight: 800; letter-spacing: 2px; margin-bottom: 12px; outline: none; }}
        .pro-input::placeholder {{ color: #475569; letter-spacing: 0; font-size: 14px; }}
        .pro-btn {{ width: 100%; background: #007A3D; color: white; border: none; padding: 14px; border-radius: 10px; font-size: 15px; font-weight: 700; cursor: pointer; }}
        .footer {{ text-align: center; padding: 20px; color: #94a3b8; font-size: 11px; }}
        .sos-banner {{ background: #dc2626; color: white; text-align: center; padding: 10px; font-weight: 700; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="sos-banner">🚨 FICHE D'URGENCE SAFELIFE — NE PAS SUPPRIMER</div>
    <div class="header">
        <div class="logo">SAFE<span>LIFE</span></div>
        <div class="badge">Fiche scannée avec succès</div>
    </div>

    <div class="container">
        <div class="alert-banner">
            <p>⚠️ En cas d'urgence, appelez le 118 immédiatement</p>
        </div>

        <div class="section">
            <h3>👤 Identité</h3>
            <div class="name">{profile.first_name} {profile.last_name}</div>
            <div class="profile-type">{"Élève" if profile.profile_type == "student" else "Adulte"} • Né(e) le {profile.birth_date} • {profile.gender}</div>
        </div>

        <div class="section" style="border-left: 4px solid #e11d48;">
            <h3>🏥 Informations médicales</h3>
            <div class="blood-badge">
                <span class="blood-label">Groupe sanguin</span>
                <span class="blood-value">{profile.blood_type or 'NC'}</span>
            </div>
            {"<div class='info-row'><span>Allergies</span><strong>" + profile.allergies + "</strong></div>" if profile.allergies else ""}
            {"<div class='info-row'><span>Maladies</span><strong>" + profile.conditions + "</strong></div>" if profile.conditions else ""}
            {"<div class='info-row'><span>Médicaments</span><strong>" + profile.medications + "</strong></div>" if profile.medications else ""}
            {"<div class='info-row'><span>Handicap</span><strong>" + profile.disabilities + "</strong></div>" if profile.disabilities else ""}
        </div>

        <div class="section">
            <h3>📞 Contacts d'urgence</h3>
            {contacts_html if contacts_html else "<p style='color:#64748b;font-size:14px'>Aucun contact renseigné</p>"}
        </div>

        {vehicle_html}
        {school_html}

        <div class="pro-section">
            <h3>🔐 Accès professionnel</h3>
            <input class="pro-input" id="proCode" placeholder="Code unité (ex: POL1717)" maxlength="12">
            <button class="pro-btn" onclick="unlockPro()">Déverrouiller l'accès complet</button>
            <div id="proResult" style="margin-top:12px;color:#94a3b8;font-size:13px;text-align:center;"></div>
        </div>
    </div>

    <div class="footer">SafeLife © 2026 — Fiche générée automatiquement<br>QR Token : {qr_token[:8]}...</div>

    <script>
    async function unlockPro() {{
        const code = document.getElementById('proCode').value.trim().toUpperCase();
        const result = document.getElementById('proResult');
        if (code.length < 4) {{ result.textContent = 'Code trop court'; return; }}
        result.textContent = 'Vérification...';
        try {{
            const res = await fetch('/scan/verify', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ token: '{qr_token}', pin: code, authority_type: 'web' }})
            }});
            const data = await res.json();
            if (res.ok) {{
                result.innerHTML = '<div style="color:#4ade80;font-weight:700">✅ Accès accordé — ' + data.authority + '</div><div style="color:white;margin-top:8px">Données complètes chargées</div>';
            }} else {{
                result.innerHTML = '<div style="color:#f87171">❌ ' + (data.detail || 'Code invalide') + '</div>';
            }}
        }} catch(e) {{
            result.textContent = 'Erreur de connexion';
        }}
    }}
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


# ─── POST /scan/verify ── Vérification code pro
@router.post("/verify")
def verify_scan(body: ScanVerifyRequest, db: Session = Depends(get_db)):
    clean_pin = body.pin.strip().upper()

    profile = db.query(Profile).filter(Profile.qr_token == body.token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    authority_name = MASTER_CODES.get(clean_pin)

    if not authority_name:
        raise HTTPException(status_code=403, detail="Code d'accès invalide")

    return {
        "status": "success",
        "authority": authority_name,
        "identity": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "birth_date": profile.birth_date,
            "gender": profile.gender,
            "nationality": profile.nationality,
        },
        "medical": {
            "blood_type": profile.blood_type or "NC",
            "allergies": profile.allergies or "Aucune",
            "conditions": profile.conditions or "Aucune",
            "medications": profile.medications or "Aucun",
            "disabilities": profile.disabilities or "Aucun",
        },
        "vehicle": {
            "has_vehicle": profile.has_vehicle,
            "type": profile.vehicle_type,
            "plate": profile.plate,
            "brand": profile.brand,
            "model": profile.model,
        },
        "emergency_contact": profile.emergency_contacts[0].phone if profile.emergency_contacts else "N/A",
        "emergency_contacts": [
            {"name": c.name, "phone": c.phone, "relation": c.relation}
            for c in profile.emergency_contacts
        ],
        "audit": {
            "authority": authority_name,
            "token": body.token[:8] + "...",
        }
    }