from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Bookings ──────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    bike_type: str       # classic | experience
    duration_type: str   # 3h | day
    booking_date: str    # YYYY-MM-DD
    booking_time: str    # HH:MM


class BookingResponse(BaseModel):
    id: int
    booking_code: str
    qr_token: str
    qr_code_base64: str
    client_name: str
    client_phone: str
    client_email: Optional[str]
    bike_type: str
    duration_type: str
    price: int
    booking_date: str
    booking_time: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Bikes ─────────────────────────────────────────────────────────────────────

class BikeCreate(BaseModel):
    name: str
    type: str            # classic | experience
    description: Optional[str] = None


class BikeUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class BikeResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Admin Auth ────────────────────────────────────────────────────────────────

class AdminLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str = "admin"
    username: str = "admin"


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "operator"    # admin | operator


class UserUpdate(BaseModel):
    password:  Optional[str]  = None
    role:      Optional[str]  = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id:        int
    username:  str
    role:      str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Events ────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: str
    time: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    max_participants: int = 0
    price: int = 0
    status: str = "active"


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    max_participants: Optional[int] = None
    price: Optional[int] = None
    status: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    date: str
    time: Optional[str]
    location: Optional[str]
    image_url: Optional[str]
    max_participants: int
    price: int
    status: str
    participants_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class RegistrationCreate(BaseModel):
    client_name: str
    client_phone: str
    client_email: Optional[str] = None


class RegistrationResponse(BaseModel):
    id: int
    event_id: int
    client_name: str
    client_phone: str
    client_email: Optional[str]
    registered_at: datetime

    class Config:
        from_attributes = True


# ── QR Scan ───────────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    token: str


class ScanResponse(BaseModel):
    success: bool
    action: str          # pickup | return | none
    message: str
    booking: Optional[dict] = None
