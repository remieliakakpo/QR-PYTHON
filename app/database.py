import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        print("✅ Base de données initialisée avec succès (SQLAlchemy).")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la DB : {e}")
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    # On l'exécute
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            # SQLAlchemy execute ne gère pas bien les scripts multi-commandes d'un coup, 
            # donc on sépare par point-virgule si nécessaire ou on utilise text()
            connection.execute(text(query))
            transaction.commit()
            print("✅ Base de données initialisée avec succès.")
        except Exception as e:
            transaction.rollback()
            print(f"❌ Erreur lors de l'initialisation de la DB : {e}")