"""Database models"""
from app.models.route_watch import RouteWatch
from app.models.price_snapshot import PriceSnapshot
from app.models.alert_log import AlertLog

__all__ = ["RouteWatch", "PriceSnapshot", "AlertLog"]
