from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    listening_history = relationship("ListeningHistory", back_populates="user")

class Wallet(Base):
    __tablename__ = "wallet"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    address = Column(String(64), nullable=False)
    seed = Column(String(256), nullable=False)
    private_key = Column(String(256))

class Track(Base):
    __tablename__ = "track"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    artist = Column(String(100), nullable=False)
    duration = Column(Integer, nullable=False)
    listening_history = relationship("ListeningHistory", back_populates="track")

class ListeningHistory(Base):
    __tablename__ = "listening_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("track.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="listening_history")
    track = relationship("Track", back_populates="listening_history")

class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(64), nullable=False)
    recipient = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)  # Изменено с Integer на Float для поддержки дробных значений
    timestamp = Column(DateTime, default=datetime.utcnow)
