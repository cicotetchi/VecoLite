import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use /tmp for Vercel serverless (ephemeral), local file for dev
# For production, set DATABASE_URL env var to a PostgreSQL/Turso URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:////tmp/vecolite.db" if os.environ.get("VERCEL") else "sqlite:///./vecolite.db"
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
