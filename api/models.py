import uuid
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """Compte admin/opérateur pour l'interface d'administration."""
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="operator")   # admin | operator
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class Bike(Base):
    __tablename__ = "bikes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)        # classic | experience
    status = Column(String, default="available") # available | in_use | maintenance
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="bike")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_code = Column(String, unique=True, index=True, nullable=False)
    qr_token = Column(String, unique=True, index=True, nullable=False)

    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=False)
    client_email = Column(String, nullable=True)

    bike_type = Column(String, nullable=False)      # classic | experience
    duration_type = Column(String, nullable=False)  # 3h | day
    price = Column(Integer, nullable=False)          # en FCFA

    bike_id = Column(Integer, ForeignKey("bikes.id"), nullable=True)
    bike = relationship("Bike", back_populates="bookings")

    booking_date = Column(String, nullable=False)  # YYYY-MM-DD
    booking_time = Column(String, nullable=False)  # HH:MM

    status = Column(String, default="pending")     # pending | active | returned | cancelled

    created_at = Column(DateTime, default=datetime.utcnow)
    pickup_at = Column(DateTime, nullable=True)
    return_at = Column(DateTime, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id          = Column(Integer, primary_key=True, index=True)
    # Token aléatoire pour les liens de partage (évite l'énumération par ID entier)
    share_token = Column(String, unique=True, nullable=True, index=True,
                         default=lambda: str(uuid.uuid4()))
    title       = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date        = Column(String, nullable=False)   # YYYY-MM-DD
    time        = Column(String, nullable=True)    # HH:MM
    location    = Column(String, nullable=True)
    image_url   = Column(String, nullable=True)
    max_participants = Column(Integer, default=0)  # 0 = illimité
    price       = Column(Integer, default=0)       # 0 = gratuit (FCFA)
    status      = Column(String, default="active") # active | draft | cancelled
    created_at  = Column(DateTime, default=datetime.utcnow)

    registrations = relationship("EventRegistration", back_populates="event",
                                 cascade="all, delete-orphan")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id          = Column(Integer, primary_key=True, index=True)
    event_id    = Column(Integer, ForeignKey("events.id"), nullable=False)
    client_name  = Column(String, nullable=False)
    client_phone = Column(String, nullable=False)
    client_email = Column(String, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="registrations")
