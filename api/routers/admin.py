import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "vecolite2024")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "vl-admin-secret-2024")


def _auth(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(401, "Non autorisé")
    return True


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=schemas.TokenResponse)
def login(creds: schemas.AdminLogin):
    if creds.username != ADMIN_USERNAME or creds.password != ADMIN_PASSWORD:
        raise HTTPException(401, "Identifiants incorrects")
    return {"access_token": ADMIN_TOKEN, "token_type": "bearer"}


# ── Dashboard stats ───────────────────────────────────────────────────────────

@router.get("/stats")
def stats(db: Session = Depends(get_db), _=Depends(_auth)):
    bookings = db.query(models.Booking).all()
    bikes = db.query(models.Bike).all()

    revenue = sum(b.price for b in bookings if b.status == "returned")

    return {
        "total_bookings": len(bookings),
        "pending": sum(1 for b in bookings if b.status == "pending"),
        "active": sum(1 for b in bookings if b.status == "active"),
        "returned": sum(1 for b in bookings if b.status == "returned"),
        "cancelled": sum(1 for b in bookings if b.status == "cancelled"),
        "total_bikes": len(bikes),
        "available_bikes": sum(1 for b in bikes if b.status == "available"),
        "in_use_bikes": sum(1 for b in bikes if b.status == "in_use"),
        "revenue": revenue,
    }


# ── Bookings ──────────────────────────────────────────────────────────────────

@router.get("/bookings")
def list_bookings(
    status: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(_auth),
):
    q = db.query(models.Booking)
    if status:
        q = q.filter(models.Booking.status == status)
    if date:
        q = q.filter(models.Booking.booking_date == date)

    rows = q.order_by(models.Booking.created_at.desc()).all()
    result = []
    for b in rows:
        bike_name = None
        if b.bike_id:
            bike = db.query(models.Bike).filter(models.Bike.id == b.bike_id).first()
            bike_name = bike.name if bike else None

        result.append({
            "id": b.id,
            "booking_code": b.booking_code,
            "client_name": b.client_name,
            "client_phone": b.client_phone,
            "client_email": b.client_email,
            "bike_type": b.bike_type,
            "duration_type": b.duration_type,
            "price": b.price,
            "booking_date": b.booking_date,
            "booking_time": b.booking_time,
            "status": b.status,
            "bike_name": bike_name,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "pickup_at": b.pickup_at.isoformat() if b.pickup_at else None,
            "return_at": b.return_at.isoformat() if b.return_at else None,
        })
    return result


@router.put("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db), _=Depends(_auth)):
    b = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not b:
        raise HTTPException(404, "Réservation introuvable")
    if b.status not in ("pending", "active"):
        raise HTTPException(400, "Impossible d'annuler cette réservation")

    if b.status == "active" and b.bike_id:
        bike = db.query(models.Bike).filter(models.Bike.id == b.bike_id).first()
        if bike:
            bike.status = "available"

    b.status = "cancelled"
    db.commit()
    return {"message": "Réservation annulée"}


# ── Bikes ─────────────────────────────────────────────────────────────────────

@router.get("/bikes")
def list_bikes(db: Session = Depends(get_db), _=Depends(_auth)):
    bikes = db.query(models.Bike).order_by(models.Bike.created_at.desc()).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "type": b.type,
            "status": b.status,
            "description": b.description,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bikes
    ]


@router.post("/bikes", response_model=schemas.BikeResponse)
def create_bike(bike: schemas.BikeCreate, db: Session = Depends(get_db), _=Depends(_auth)):
    db_bike = models.Bike(
        name=bike.name,
        type=bike.type,
        description=bike.description,
        status="available",
    )
    db.add(db_bike)
    db.commit()
    db.refresh(db_bike)
    return db_bike


@router.put("/bikes/{bike_id}")
def update_bike(
    bike_id: int,
    data: schemas.BikeUpdate,
    db: Session = Depends(get_db),
    _=Depends(_auth),
):
    bike = db.query(models.Bike).filter(models.Bike.id == bike_id).first()
    if not bike:
        raise HTTPException(404, "Vélo introuvable")
    if data.name is not None:
        bike.name = data.name
    if data.type is not None:
        bike.type = data.type
    if data.status is not None:
        bike.status = data.status
    if data.description is not None:
        bike.description = data.description
    db.commit()
    db.refresh(bike)
    return {
        "id": bike.id,
        "name": bike.name,
        "type": bike.type,
        "status": bike.status,
        "description": bike.description,
    }


@router.delete("/bikes/{bike_id}")
def delete_bike(bike_id: int, db: Session = Depends(get_db), _=Depends(_auth)):
    bike = db.query(models.Bike).filter(models.Bike.id == bike_id).first()
    if not bike:
        raise HTTPException(404, "Vélo introuvable")
    db.delete(bike)
    db.commit()
    return {"message": "Vélo supprimé"}
