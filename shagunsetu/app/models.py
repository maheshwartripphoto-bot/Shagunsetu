from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    groom_name = Column(String, nullable=False)
    bride_name = Column(String, nullable=False)
    event_date = Column(String, nullable=False)
    muhurat_time = Column(String, nullable=True)
    venue = Column(String, nullable=False)
    host_family = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Bi-directional link to all RSVPs submitted by guests
    rsvps = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")


class RSVP(Base):
    __tablename__ = "rsvps"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    guest_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    attending = Column(String, default="Yes")  # "Yes" or "No"
    guest_count = Column(Integer, default=1)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="rsvps")
