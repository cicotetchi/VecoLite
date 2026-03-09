import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from mangum import Mangum

from .database import engine, Base
from .routers import bookings, admin, scan

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VecoLite API",
    description="API de location de vélos — système QR double scan",
    version="1.0.0",
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


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "VecoLite"}


# Serve static frontend in dev only (Vercel serves public/ via CDN in production)
if not os.environ.get("VERCEL"):
    _public = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
    if os.path.isdir(_public):
        app.mount("/admin", StaticFiles(directory=os.path.join(_public, "admin"), html=True), name="admin")
        app.mount("/", StaticFiles(directory=_public, html=True), name="static")


# Vercel serverless handler
handler = Mangum(app, lifespan="off")
