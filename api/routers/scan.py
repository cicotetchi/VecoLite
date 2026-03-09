from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("/", response_model=schemas.ScanResponse)
def process_scan(scan: schemas.ScanRequest, db: Session = Depends(get_db)):
    # Token may arrive raw or prefixed "VECOLITE:<token>"
    token = scan.token.replace("VECOLITE:", "").strip()

    booking = db.query(models.Booking).filter(models.Booking.qr_token == token).first()
    if not booking:
        raise HTTPException(404, "QR code invalide — réservation introuvable")

    # ── Cancelled ──────────────────────────────────────────────────────────────
    if booking.status == "cancelled":
        return schemas.ScanResponse(
            success=False,
            action="none",
            message="Cette réservation a été annulée.",
            booking=_booking_dict(booking),
        )

    # ── Already returned ───────────────────────────────────────────────────────
    if booking.status == "returned":
        return schemas.ScanResponse(
            success=False,
            action="none",
            message="Ce vélo a déjà été rendu. Merci !",
            booking=_booking_dict(booking),
        )

    # ── PICKUP (pending → active) ──────────────────────────────────────────────
    if booking.status == "pending":
        bike = (
            db.query(models.Bike)
            .filter(models.Bike.type == booking.bike_type, models.Bike.status == "available")
            .first()
        )
        if not bike:
            return schemas.ScanResponse(
                success=False,
                action="pickup",
                message=f"Aucun vélo {booking.bike_type} disponible pour l'instant.",
                booking=_booking_dict(booking),
            )

        booking.status = "active"
        booking.bike_id = bike.id
        booking.pickup_at = datetime.utcnow()
        bike.status = "in_use"
        db.commit()

        return schemas.ScanResponse(
            success=True,
            action="pickup",
            message=f"✓ Vélo « {bike.name} » remis à {booking.client_name}.",
            booking={**_booking_dict(booking), "bike_name": bike.name},
        )

    # ── RETURN (active → returned) ─────────────────────────────────────────────
    if booking.status == "active":
        duration_str = None
        if booking.pickup_at:
            diff = datetime.utcnow() - booking.pickup_at
            h = int(diff.total_seconds() // 3600)
            m = int((diff.total_seconds() % 3600) // 60)
            duration_str = f"{h}h{m:02d}"

        if booking.bike_id:
            bike = db.query(models.Bike).filter(models.Bike.id == booking.bike_id).first()
            if bike:
                bike.status = "available"

        booking.status = "returned"
        booking.return_at = datetime.utcnow()
        db.commit()

        return schemas.ScanResponse(
            success=True,
            action="return",
            message=f"✓ Vélo rendu par {booking.client_name}. Durée : {duration_str or 'N/A'}.",
            booking={**_booking_dict(booking), "duration": duration_str},
        )

    return schemas.ScanResponse(success=False, action="none", message="État inconnu.")


def _booking_dict(b: models.Booking) -> dict:
    return {
        "id": b.id,
        "booking_code": b.booking_code,
        "client_name": b.client_name,
        "client_phone": b.client_phone,
        "bike_type": b.bike_type,
        "duration_type": b.duration_type,
        "price": b.price,
        "booking_date": b.booking_date,
        "booking_time": b.booking_time,
        "status": b.status,
    }
