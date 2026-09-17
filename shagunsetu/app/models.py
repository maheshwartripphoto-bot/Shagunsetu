import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from .database import Base


def gen_id():
    return uuid.uuid4().hex[:12]


class Wedding(Base):
    __tablename__ = "weddings"

    id = Column(String, primary_key=True, default=gen_id)
    slug = Column(String, unique=True, index=True, nullable=False)

    bride_name = Column(String, nullable=False)
    groom_name = Column(String, nullable=False)
    bride_family = Column(String, default="")
    groom_family = Column(String, default="")
    wedding_date = Column(String, nullable=False)  # ISO date
    venue = Column(String, default="")
    city = Column(String, default="")
    description = Column(Text, default="")
    cover_image = Column(String, default="")

    invitation_title = Column(String, default="")
    invocation = Column(String, default="|| \u0936\u094d\u0930\u0940 \u0917\u0923\u0947\u0936\u093e\u092f \u0928\u092e\u0903 ||")

    upi_id = Column(String, default="")
    upi_name = Column(String, default="")
    whatsapp_contact = Column(String, default="")

    enable_shagun = Column(Boolean, default=True)
    enable_token = Column(Boolean, default=True)

    theme = Column(String, default="classic")

    admin_pin = Column(String, default="1234")  # simple demo auth

    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="wedding", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="wedding", cascade="all, delete-orphan")
    rsvps = relationship("RSVP", back_populates="wedding", cascade="all, delete-orphan")
    shaguns = relationship("Shagun", back_populates="wedding", cascade="all, delete-orphan")
    blessings = relationship("Blessing", back_populates="wedding", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=gen_id)
    wedding_id = Column(String, ForeignKey("weddings.id"))
    name = Column(String, nullable=False)
    date = Column(String, default="")
    time = Column(String, default="")
    venue = Column(String, default="")
    dress_code = Column(String, default="")
    muhurat = Column(String, default="")
    maps_url = Column(String, default="")

    wedding = relationship("Wedding", back_populates="events")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(String, primary_key=True, default=gen_id)
    wedding_id = Column(String, ForeignKey("weddings.id"))
    title = Column(String, nullable=False)
    target_amount = Column(Float, default=0)
    raised_amount = Column(Float, default=0)
    category = Column(String, default="Other")
    gift_type = Column(String, default="Exclusive Gift")  # or "Group Gift"
    is_claimed = Column(Boolean, default=False)
    claimed_by = Column(String, default="")

    wedding = relationship("Wedding", back_populates="wishlist_items")


class RSVP(Base):
    __tablename__ = "rsvps"

    id = Column(String, primary_key=True, default=gen_id)
    wedding_id = Column(String, ForeignKey("weddings.id"))
    guest_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    attending = Column(Boolean, default=True)
    adult_count = Column(Integer, default=1)
    child_count = Column(Integer, default=0)
    events = Column(String, default="")  # comma-separated event ids
    diet = Column(String, default="Pure Vegetarian")
    message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    wedding = relationship("Wedding", back_populates="rsvps")


class Shagun(Base):
    __tablename__ = "shaguns"

    id = Column(String, primary_key=True, default=gen_id)
    wedding_id = Column(String, ForeignKey("weddings.id"))
    sender_name = Column(String, nullable=False)
    amount = Column(Float, default=0)
    token_included = Column(Boolean, default=False)
    message = Column(Text, default="")
    payment_status = Column(String, default="initiated")  # initiated | unverified
    created_at = Column(DateTime, default=datetime.utcnow)

    wedding = relationship("Wedding", back_populates="shaguns")


class Blessing(Base):
    __tablename__ = "blessings"

    id = Column(String, primary_key=True, default=gen_id)
    wedding_id = Column(String, ForeignKey("weddings.id"))
    name = Column(String, default="A well-wisher")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    wedding = relationship("Wedding", back_populates="blessings")
