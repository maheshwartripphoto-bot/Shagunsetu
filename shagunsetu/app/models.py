from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    groom_name = Column(String, nullable=False)
    bride_name = Column(String, nullable=False)
    wedding_date = Column(String, nullable=False)
    venue = Column(String, nullable=False)
    host_family = Column(String, nullable=True)
    upi_id = Column(String, nullable=False)
    upi_payee_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ceremonies = relationship("Ceremony", back_populates="event", cascade="all, delete-orphan")
    rsvps = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")
    registry_items = relationship("RegistryItem", back_populates="event", cascade="all, delete-orphan")
    shagun_transactions = relationship("ShagunEntry", back_populates="event", cascade="all, delete-orphan")


class Ceremony(Base):
    __tablename__ = "ceremonies"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    venue_name = Column(String, nullable=False)
    maps_url = Column(String, nullable=True)
    dress_code = Column(String, nullable=True)

    event = relationship("Event", back_populates="ceremonies")


class RSVP(Base):
    __tablename__ = "rsvps"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    guest_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    attending = Column(String, default="Yes")
    guest_count = Column(Integer, default=1)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="rsvps")


class RegistryItem(Base):
    __tablename__ = "registry_items"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    item_name = Column(String, nullable=False)
    category = Column(String, default="Home")
    target_amount = Column(Float, nullable=False)
    collected_amount = Column(Float, default=0.0)
    is_claimed = Column(Boolean, default=False)
    claimed_by = Column(String, nullable=True)

    event = relationship("Event", back_populates="registry_items")


class ShagunEntry(Base):
    __tablename__ = "shagun_entries"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    sender_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    blessing_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="shagun_transactions")
