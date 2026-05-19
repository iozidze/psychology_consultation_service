from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    specialization = Column(String(255), nullable=True)
    education = Column(Text, nullable=True)
    about = Column(Text, nullable=True)
    rating = Column(Float, default=0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    psychologist_slots = relationship(
        "Slot",
        foreign_keys="Slot.psychologist_id",
        back_populates="psychologist",
    )
    client_slots = relationship(
        "Slot",
        foreign_keys="Slot.client_id",
        back_populates="client",
    )


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    psychologist_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    start_at = Column(DateTime, index=True, nullable=False)
    end_at = Column(DateTime, index=True, nullable=False)
    specialization = Column(String(255), nullable=False)
    meeting_link = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    psychologist = relationship(
        "User",
        foreign_keys=[psychologist_id],
        back_populates="psychologist_slots",
    )
    client = relationship("User", foreign_keys=[client_id], back_populates="client_slots")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    kind = Column(String(32), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    author = relationship("User", foreign_keys=[author_id])
    client = relationship("User", foreign_keys=[client_id])


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    psychologist_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    psychologist = relationship("User", foreign_keys=[psychologist_id])
    client = relationship("User", foreign_keys=[client_id])


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("psychologist_id", "client_id", name="uq_review_pair"),)

    id = Column(Integer, primary_key=True, index=True)
    psychologist_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    psychologist = relationship("User", foreign_keys=[psychologist_id])
    client = relationship("User", foreign_keys=[client_id])
