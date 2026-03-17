"""Modelo de log de alerta"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AlertLog(Base):
    """Modelo de log de alerta enviado ao usuário"""
    __tablename__ = "alert_logs"
    
    id = Column(Integer, primary_key=True)
    route_watch_id = Column(Integer, ForeignKey("route_watches.id"), nullable=False)
    price_snapshot_id = Column(Integer, ForeignKey("price_snapshots.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    route_watch = relationship("RouteWatch", back_populates="alerts")
    snapshot = relationship("PriceSnapshot", back_populates="alerts")
