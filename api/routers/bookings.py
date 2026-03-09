import uuid
import io
import base64
from datetime import datetime

import qrcode
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

PRICING = {
    ("classic", "3h"):  5_000,
    ("classic", "day"): 10_000,
    ("experience", "3h"):  7_000,
    ("experience", "day"): 12_000,
}

BIKE_TYPE_LABELS = {
    "classic": "Vélo Classique",
    "experience": "Vélo Expérience",
}
DURATION_LABELS = {
    "3h": "3 Heures",
    "day": "Journée complète",
}


def _make_booking_code(db: Session) -> str:
    year = datetime.now().year
    count = db.query(models.Booking).count() + 1
    return f"VL-{year}-{count:04d}"


def _make_qr_png_b64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1C3A22", back_color="#F2EBD9")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@router.post("/", response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    price = PRICING.get((booking.bike_type, booking.duration_type))
    if price is None:
        raise HTTPException(400, "Type de vélo ou durée invalide")

    token = str(uuid.uuid4())
    code = _make_booking_code(db)

    # QR encodes a scannable string; admin app parses the token part
    qr_data = f"VECOLITE:{token}"
    qr_b64 = _make_qr_png_b64(qr_data)

    db_booking = models.Booking(
        booking_code=code,
        qr_token=token,
        client_name=booking.client_name,
        client_phone=booking.client_phone,
        client_email=booking.client_email,
        bike_type=booking.bike_type,
        duration_type=booking.duration_type,
        price=price,
        booking_date=booking.booking_date,
        booking_time=booking.booking_time,
        status="pending",
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return schemas.BookingResponse(
        id=db_booking.id,
        booking_code=db_booking.booking_code,
        qr_token=db_booking.qr_token,
        qr_code_base64=qr_b64,
        client_name=db_booking.client_name,
        client_phone=db_booking.client_phone,
        client_email=db_booking.client_email,
        bike_type=db_booking.bike_type,
        duration_type=db_booking.duration_type,
        price=db_booking.price,
        booking_date=db_booking.booking_date,
        booking_time=db_booking.booking_time,
        status=db_booking.status,
        created_at=db_booking.created_at,
    )


@router.get("/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    b = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not b:
        raise HTTPException(404, "Réservation introuvable")
    return {
        "id": b.id,
        "booking_code": b.booking_code,
        "client_name": b.client_name,
        "bike_type": b.bike_type,
        "duration_type": b.duration_type,
        "price": b.price,
        "booking_date": b.booking_date,
        "booking_time": b.booking_time,
        "status": b.status,
    }
