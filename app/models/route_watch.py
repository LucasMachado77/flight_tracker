"""Modelo de rota monitorada"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class RouteWatch(Base):
    """Modelo de rota monitorada para rastreamento de preços de voos"""
    __tablename__ = "route_watches"
    
    id = Column(Integer, primary_key=True)
    origin = Column(String(3), nullable=False)  # Código IATA
    destination = Column(String(3), nullable=False)
    departure_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=False)
    adults = Column(Integer, nullable=False, default=1)
    cabin_class = Column(String(20), nullable=False, default="ECONOMY")
    max_stops = Column(Integer, nullable=True)
    currency = Column(String(3), nullable=False, default="EUR")
    check_interval_minutes = Column(Integer, nullable=False, default=360)
    notify_on_new_low = Column(Boolean, nullable=False, default=True)
    target_price = Column(Float, nullable=True)
    min_price_difference = Column(Float, nullable=True)
    alert_cooldown_hours = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    flexible_dates = Column(Boolean, nullable=False, default=True)  # True = flexível, False = exata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    snapshots = relationship("PriceSnapshot", back_populates="route_watch")
    alerts = relationship("AlertLog", back_populates="route_watch")
