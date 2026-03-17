"""Modelo de snapshot de preço"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class PriceSnapshot(Base):
    """Modelo de snapshot de preço de voo em momento específico"""
    __tablename__ = "price_snapshots"
    
    id = Column(Integer, primary_key=True)
    route_watch_id = Column(Integer, ForeignKey("route_watches.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    searched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    price_total = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    airline = Column(String(100), nullable=True)
    airline_code = Column(String(10), nullable=True)
    departure_at = Column(String(50), nullable=True)
    return_at = Column(String(50), nullable=True)
    stops = Column(Integer, nullable=True)
    offer_hash = Column(String(200), nullable=True)
    raw_response_json = Column(JSON, nullable=False)
    
    # Relationships
    route_watch = relationship("RouteWatch", back_populates="snapshots")
    alerts = relationship("AlertLog", back_populates="snapshot")
