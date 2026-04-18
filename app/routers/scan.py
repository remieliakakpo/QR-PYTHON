# ─── POST /scan/verify ── Vérification ultra-robuste
@router.post("/verify")
def verify_scan(body: ScanVerifyRequest, db: Session = Depends(get_db)):
    # 1. Logs de débogage (Regarde tes logs Railway !)
    print(f"DEBUG: Token reçu = {body.token}")
    print(f"DEBUG: PIN reçu = '{body.pin}'")

    # 2. Nettoyage strict
    clean_pin = str(body.pin).strip().upper()
    
    # 3. Recherche du profil (On cherche par qr_token OU par ID au cas où)
    profile = db.query(Profile).filter(
        (Profile.qr_token == body.token) | (Profile.id == body.token)
    ).first()
    
    if not profile:
        print("DEBUG: Profil non trouvé en base")
        raise HTTPException(status_code=404, detail="Profil introuvable")

    # 4. Vérification codes maîtres
    authority_name = MASTER_CODES.get(clean_pin)
    
    # 5. Si pas de code maître, vérification du code personnel
    if not authority_name:
        # On récupère le code du profil, par défaut 1234
        user_pin = str(getattr(profile, 'access_code', '1234')).strip().upper()
        if clean_pin == user_pin:
            authority_name = "Accès Privé (Code Personnel)"

    if not authority_name:
        print(f"DEBUG: Échec de comparaison. Saisi: {clean_pin}")
        raise HTTPException(status_code=403, detail="CODE INVALIDE POUR CETTE UNITE")

    print(f"DEBUG: Succès ! Unité: {authority_name}")

    # 6. Retourne la structure EXACTE attendue par ton ScanResultScreen.tsx
    return {
        "status": "success",
        "authority": authority_name,
        "identity": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "birth_date": profile.birth_date or "Non renseignée",
            "gender": profile.gender or "NC",
            "nationality": getattr(profile, 'nationality', 'Togolaise'),
        },
        "medical": {
            "blood_type": profile.blood_type or "NC",
            "allergies": profile.allergies or "Aucune",
            "conditions": profile.conditions or "Aucune",
            "medications": profile.medications or "Aucun",
            "disabilities": profile.disabilities or "Aucun",
        },
        "vehicle": {
            "has_vehicle": getattr(profile, 'has_vehicle', False),
            "type": getattr(profile, 'vehicle_type', None),
            "plate": getattr(profile, 'plate', None),
            "brand": getattr(profile, 'brand', None),
            "model": getattr(profile, 'model', None),
        },
        "emergency_contacts": [
            {"name": c.name, "phone": c.phone, "relation": c.relation}
            for c in profile.emergency_contacts
        ] if profile.emergency_contacts else [],
        "audit": {
            "authority": authority_name,
            "token": body.token[:8]
        }
    }