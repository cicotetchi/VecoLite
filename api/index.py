import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Vercel compatibility: relative imports require the package to be recognised.
# Fallback to absolute imports when running as a flat module.
try:
    from .database import engine, Base, SessionLocal
    from .routers import bookings, admin, scan, events, users
    from .models import User
    from .auth import hash_password
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import engine, Base, SessionLocal   # noqa: E402
    from routers import bookings, admin, scan, events, users  # noqa: E402
    from models import User                           # noqa: E402
    from auth import hash_password                    # noqa: E402

# ── Create tables ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)


# ── Ensure a default admin account exists ─────────────────────────────────────
def _bootstrap_admin():
    """Creates the default admin account if no admin user exists yet."""
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == "admin").first():
            db.add(User(
                username=os.environ.get("ADMIN_USERNAME", "admin"),
                password_hash=hash_password(os.environ.get("ADMIN_PASSWORD", "vecolite2024")),
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
