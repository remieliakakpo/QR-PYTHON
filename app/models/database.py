# app/models/database.py
from sqlalchemy.ext.declarative import declarative_base

# On définit un Base factice pour que l'import fonctionne
Base = declarative_base()

def get_db():
    yield None