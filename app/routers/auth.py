@router.post("/register") # Enlève le response_model temporairement pour débugger
def register(data: UserRegister, db: Session = Depends(get_db)):
    print(f"DEBUG: Tentative d'inscription avec le numéro: {data.phone}")
    
    # Vérifier si téléphone existe déjà
    existing_user = db.query(User).filter(User.phone == data.phone).first()
    if existing_user:
        print("DEBUG: Numéro déjà utilisé")
        raise HTTPException(status_code=400, detail="Ce numéro est déjà utilisé")

    try:
        user = User(
            id=str(uuid.uuid4()),
            phone=data.phone,
            password=hash_password(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        token = create_token(user.id)
        return {"message": "Compte créé", "token": token, "user": {"id": user.id, "phone": user.phone}}
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne serveur")