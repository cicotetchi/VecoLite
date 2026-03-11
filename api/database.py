import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

# ── Résolution de l'URL de base de données ────────────────────────────────
_raw_url = os.environ.get("DATABASE_URL", "")

if _raw_url:
    # Normalisation : Supabase/Heroku renvoient parfois "postgres://"
    # mais SQLAlchemy 2.x exige "postgresql://"
    DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)
    IS_POSTGRES = True
else:
    # Fallback local : SQLite
    DATABASE_URL = (
        "sqlite:////tmp/vecolite.db"
        if os.environ.get("VERCEL")
        else "sqlite:///./vecolite.db"
    )
    IS_POSTGRES = False

# ── Création du moteur ────────────────────────────────────────────────────
if IS_POSTGRES:
    # NullPool : indispensable en serverless (Vercel) pour éviter
    # les connexions fantômes entre invocations Lambda
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
