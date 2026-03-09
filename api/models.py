from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


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
