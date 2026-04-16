@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    # 1. Vérification téléphone
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="Ce numéro est déjà utilisé")

    try:
        # 2. Création de l'utilisateur
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            phone=data.phone,
            password=hash_password(data.password),
        )
        db.add(new_user)

        # 3. CRÉATION DU PROFIL (Avec TOUS les champs obligatoires)
        generated_qr_token = str(uuid.uuid4())[:8].upper()
        
        new_profile = Profile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            qr_token=generated_qr_token,
            profile_type="CITIZEN",    # OBLIGATOIRE (nullable=False)
            first_name="Utilisateur",  # OBLIGATOIRE
            last_name="SafeMe",       # OBLIGATOIRE
            birth_date="01/01/2000",   # OBLIGATOIRE
            gender="M",                # OBLIGATOIRE
            nationality="Togo",        # OBLIGATOIRE
            blood_type="NC",           # OBLIGATOIRE
            access_code="1234",
            has_vehicle=False
        )
        db.add(new_profile)

        db.commit()
        db.refresh(new_user)
        
        token = create_token(new_user.id)
        return {
            "message": "Compte créé", 
            "token": token, 
            "user": {
                "id": new_user.id, 
                "phone": new_user.phone,
                "qr_token": generated_qr_token
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERREUR CRITIQUE: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création du profil")