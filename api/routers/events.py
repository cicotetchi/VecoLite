from typing import Optional
from datetime import datetime
import os, uuid as _uuid
import urllib.request, urllib.error

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import require_auth, require_admin

router = APIRouter(tags=["events"])


def _event_to_dict(event: models.Event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date,
        "time": event.time,
        "location": event.location,
        "image_url": event.image_url,
        "max_participants": event.max_participants,
        "price": event.price,
        "status": event.status,
        "participants_count": len(event.registrations),
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


# ── Public ────────────────────────────────────────────────────────────────────

@router.get("/api/events")
def list_public_events(db: Session = Depends(get_db)):
    """Retourne les événements actifs, triés par date."""
    events = (
        db.query(models.Event)
        .filter(models.Event.status == "active")
        .order_by(models.Event.date.asc())
        .all()
    )
    return [_event_to_dict(e) for e in events]


@router.post("/api/events/{event_id}/register")
def register_for_event(
    event_id: int,
    data: schemas.RegistrationCreate,
    db: Session = Depends(get_db),
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Événement introuvable")
    if event.status != "active":
        raise HTTPException(400, "Les inscriptions sont fermées pour cet événement")

    count = len(event.registrations)
    if event.max_participants > 0 and count >= event.max_participants:
        raise HTTPException(400, "Événement complet")

    reg = models.EventRegistration(
        event_id=event_id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        client_email=data.client_email,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return {
        "success": True,
        "message": f"Inscription confirmée pour « {event.title} »",
        "registration_id": reg.id,
    }


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/api/admin/events")
def admin_list_events(db: Session = Depends(get_db), _=Depends(require_auth)):
    events = db.query(models.Event).order_by(models.Event.date.asc()).all()
    return [_event_to_dict(e) for e in events]


@router.post("/api/admin/events")
def admin_create_event(
    data: schemas.EventCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    event = models.Event(
        title=data.title,
        description=data.description,
        date=data.date,
        time=data.time,
        location=data.location,
        image_url=data.image_url,
        max_participants=data.max_participants,
        price=data.price,
        status=data.status,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_to_dict(event)


@router.put("/api/admin/events/{event_id}")
def admin_update_event(
    event_id: int,
    data: schemas.EventUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Événement introuvable")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return _event_to_dict(event)


@router.delete("/api/admin/events/{event_id}")
def admin_delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),   # ⛔ admin seulement
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Événement introuvable")
    db.delete(event)
    db.commit()
    return {"message": "Événement supprimé"}


@router.post("/api/admin/events/upload")
async def upload_event_media(
    file: UploadFile = File(...),
    _=Depends(require_auth),
):
    """Upload une image ou vidéo vers Supabase Storage et retourne l'URL publique."""
    supabase_url = os.environ.get("SUPABASE_URL", "https://xlpypozfpuemuanhnoxh.supabase.co")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not supabase_key:
        raise HTTPException(500, "SUPABASE_SERVICE_KEY non configuré côté serveur")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 Mo max
        raise HTTPException(400, "Fichier trop volumineux (max 50 Mo)")

    ext = ""
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
    filename = f"events/{_uuid.uuid4().hex}{ext}"
    content_type = file.content_type or "application/octet-stream"

    bucket = "assets"
    upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"
    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "apikey": supabase_key,
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    req = urllib.request.Request(upload_url, data=content, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            r.read()
    except urllib.error.HTTPError as e:
        raise HTTPException(500, f"Erreur Supabase Storage : {e.read().decode()}")

    public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"
    return {"url": public_url, "filename": filename}


@router.get("/api/admin/events/{event_id}/registrations")
def admin_event_registrations(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Événement introuvable")
    return {
        "event": _event_to_dict(event),
        "registrations": [
            {
                "id": r.id,
                "client_name": r.client_name,
                "client_phone": r.client_phone,
                "client_email": r.client_email,
                "registered_at": r.registered_at.isoformat() if r.registered_at else None,
            }
            for r in event.registrations
        ],
    }
