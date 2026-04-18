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

# Codes maîtres pour les unités d'urgence du Togo/Bénin
MASTER_CODES = {
    "POL1717": "Police Nationale",
    "AMBU1818": "Service d'Ambulance",
    "POMP2626": "Sapeurs-Pompiers",
    "MEDC3737": "Corps Médical",
}

@router.get("/{qr_token}", response_class=HTMLResponse)
def public_profile(qr_token: str, request: Request, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.qr_token == qr_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil SafeLife introuvable")

    # Enregistrement du log de scan
    scan = Scan(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        scanner_ip=request.client.host if request.client else None,
        alert_sent=False,
    )
    db.add(scan)
    db.commit()

    # Génération dynamique des contacts
    contacts_html = "".join([f"""
        <div class="contact-card">
            <div class="contact-info">
                <span class="contact-name">{c.name}</span>
                <span class="contact-relation">{c.relation or 'Contact'}</span>
            </div>
            <a href="tel:{c.phone}" class="call-btn">📞 {c.phone}</a>
        </div>""" for c in profile.emergency_contacts])

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeLife — Fiche d'urgence</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f8fafc; color: #1e293b; }}
        .sos-banner {{ background: #be123c; color: white; text-align: center; padding: 8px; font-weight: 800; font-size: 12px; }}
        .header {{ background: #007A3D; padding: 30px 20px; text-align: center; color: white; }}
        .container {{ max-width: 500px; margin: 0 auto; padding: 15px; }}
        .section {{ background: white; border-radius: 15px; padding: 20px; margin-bottom: 15px; shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .section h3 {{ font-size: 12px; color: #64748b; text-transform: uppercase; margin-bottom: 15px; border-bottom: 1px solid #f1f5f9; padding-bottom: 5px; }}
        .name {{ font-size: 24px; font-weight: 800; }}
        .blood-badge {{ background: #fff1f2; border: 2px solid #fda4af; border-radius: 15px; padding: 15px; text-align: center; margin: 10px 0; }}
        .blood-value {{ font-size: 32px; font-weight: 900; color: #e11d48; }}
        .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f8fafc; font-size: 14px; }}
        .contact-card {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }}
        .call-btn {{ background: #007A3D; color: white; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-weight: 700; }}
        
        /* Section Pro */
        .pro-box {{ background: #0f172a; border-radius: 15px; padding: 20px; color: white; }}
        .pro-input {{ width: 100%; padding: 15px; border-radius: 10px; border: 1px solid #334155; background: #1e293b; color: white; font-size: 18px; text-align: center; margin-bottom: 10px; }}
        .pro-btn {{ width: 100%; background: #007A3D; color: white; border: none; padding: 15px; border-radius: 10px; font-weight: 700; cursor: pointer; }}
        .hidden-data {{ display: none; margin-top: 15px; background: #1e293b; padding: 15px; border-radius: 10px; border-left: 4px solid #4ade80; }}
    </style>
</head>
<body>
    <div class="sos-banner">🚨 INTERVENTION D'URGENCE — SAFELIFE</div>
    <div class="header">
        <h1>SAFE<span style="color:#FFCD00">LIFE</span></h1>
        <p>Identité Numérique de Secours</p>
    </div>

    <div class="container">
        <div class="section">
            <h3>👤 Identité de base</h3>
            <div class="name">{profile.first_name} {profile.last_name}</div>
            <div style="color:#64748b">Né(e) le {profile.birth_date or 'NC'}</div>
        </div>

        <div class="section">
            <h3>🏥 Médical (Public)</h3>
            <div class="blood-badge">
                <div style="font-size:10px; color:#e11d48; font-weight:800">GROUPE SANGUIN</div>
                <div class="blood-value">{profile.blood_type or 'NC'}</div>
            </div>
        </div>

        <div class="section">
            <h3>📞 Contacts d'urgence</h3>
            {contacts_html or "<p>Aucun contact</p>"}
        </div>

        <div class="pro-box">
            <h3>🔐 Accès Unité d'Urgence</h3>
            <p style="font-size:12px; color:#94a3b8; margin-bottom:10px;">Réservé Police, SAMU, Sapeurs-Pompiers</p>
            <input type="text" id="pinCode" class="pro-input" placeholder="Code Unité (ex: POL1717)">
            <button class="pro-btn" onclick="verifyPro()">DÉVERROUILLER LES DONNÉES</button>
            
            <div id="proDetails" class="hidden-data">
                <h4 style="color:#4ade80">✅ Accès Autorisé</h4>
                <div id="medicalFull" style="font-size:14px; margin-top:10px; line-height:1.6"></div>
            </div>
        </div>
    </div>

    <script>
    async function verifyPro() {{
        const pin = document.getElementById('pinCode').value.trim().toUpperCase();
        const detailsBox = document.getElementById('proDetails');
        const medicalFull = document.getElementById('medicalFull');
        
        try {{
            const response = await fetch('/scan/verify', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ token: '{qr_token}', pin: pin }})
            }});
            
            const data = await response.json();
            
            if (response.ok) {{
                detailsBox.style.display = 'block';
                medicalFull.innerHTML = `
                    <p><strong>Unité :</strong> ${{data.authority}}</p>
                    <hr style="border:0; border-top:1px solid #334155; margin:10px 0">
                    <p><strong>Allergies :</strong> ${{data.medical.allergies}}</p>
                    <p><strong>Maladies :</strong> ${{data.medical.conditions}}</p>
                    <p><strong>Médicaments :</strong> ${{data.medical.medications}}</p>
                    <p><strong>Handicap :</strong> ${{data.medical.disabilities}}</p>
                `;
                document.getElementById('pinCode').style.display = 'none';
                document.querySelector('.pro-btn').style.display = 'none';
            }} else {{
                alert(data.detail || "Code invalide");
            }}
        }} catch (e) {{
            alert("Erreur de connexion au serveur");
        }}
    }}
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)
@router.post("/verify")
def verify_scan(body: ScanVerifyRequest, db: Session = Depends(get_db)):
    # Nettoyage strict
    clean_pin = body.pin.strip().upper()
    
    profile = db.query(Profile).filter(Profile.qr_token == body.token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # 1. Vérification codes maîtres (POL1717, AMBU1818, etc.)
    authority_name = MASTER_CODES.get(clean_pin)
    
    # 2. Vérification code personnel (si pas de code maître)
    if not authority_name:
        user_pin = str(getattr(profile, 'access_code', '1234')).strip().upper()
        if clean_pin == user_pin:
            authority_name = "Accès Privé (Code Personnel)"

    if not authority_name:
        raise HTTPException(status_code=403, detail="CODE INVALIDE POUR CETTE UNITE")

    return {
        "status": "success",
        "authority": authority_name,
        "medical": {
            "blood_type": profile.blood_type or "NC",
            "allergies": profile.allergies or "Aucune",
            "conditions": profile.conditions or "Aucune",
            "medications": profile.medications or "Aucun",
            "disabilities": profile.disabilities or "Aucun",
        }
    }