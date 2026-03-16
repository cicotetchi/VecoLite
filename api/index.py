import os
import sys
import uuid as _uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Vercel compatibility: relative imports require the package to be recognised.
# Fallback to absolute imports when running as a flat module.
try:
    from .database import engine, Base, SessionLocal
    from .routers import bookings, admin, scan, events, users
    from .models import User, Event
    from .auth import hash_password
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import engine, Base, SessionLocal   # noqa: E402
    from routers import bookings, admin, scan, events, users  # noqa: E402
    from models import User, Event                    # noqa: E402
    from auth import hash_password                    # noqa: E402

# ── Create tables ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)


# ── Migration : ajoute share_token aux événements existants ───────────────────
def _migrate_share_tokens():
    """Ajoute la colonne share_token si absente, puis backfille les événements."""
    from sqlalchemy import text
    # 1. Ajouter la colonne si elle n'existe pas encore (idempotent)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE events ADD COLUMN share_token VARCHAR"))
            conn.commit()
        except Exception:
            pass  # déjà présente
    # 2. Backfiller les événements sans token
    db = SessionLocal()
    try:
        missing = db.query(Event).filter(Event.share_token.is_(None)).all()
        for ev in missing:
            ev.share_token = str(_uuid.uuid4())
        if missing:
            db.commit()
    finally:
        db.close()


_migrate_share_tokens()


# ── Ensure a default admin account exists ─────────────────────────────────────
def _bootstrap_admin():
    """Creates the default admin account if no admin user exists yet.
    Requires ADMIN_USERNAME and ADMIN_PASSWORD env vars — skipped if absent.
    """
    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        return  # variables d'environnement non définies → on ne crée rien

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == "admin").first():
            db.add(User(
                username=admin_username,
                password_hash=hash_password(admin_password),
                role="admin",
            ))
            db.commit()
    finally:
        db.close()


_bootstrap_admin()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="VecoLite API",
    description="API de location de vélos — système QR double scan",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bookings.router)
app.include_router(admin.router)
app.include_router(scan.router)
app.include_router(events.router)
app.include_router(users.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "VecoLite", "version": "2.0.0"}


# Serve static frontend in dev only (Vercel serves public/ via CDN in production)
if not os.environ.get("VERCEL"):
    _public = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
    if os.path.isdir(_public):
        app.mount("/admin", StaticFiles(directory=os.path.join(_public, "admin"), html=True), name="admin")
        app.mount("/", StaticFiles(directory=_public, html=True), name="static")

# Vercel Python runtime détecte nativement les apps ASGI (FastAPI/Starlette).
# Mangum n'est plus nécessaire et causait un TypeError dans vc_init.py.
