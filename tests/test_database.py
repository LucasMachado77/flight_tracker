"""Tests for database configuration"""
import pytest
from sqlalchemy import inspect
from app.core.database import engine, get_session, create_tables, Base
from app.models.route_watch import RouteWatch
from app.models.price_snapshot import PriceSnapshot
from app.models.alert_log import AlertLog


def test_engine_created():
    """Test that SQLAlchemy engine is created"""
    assert engine is not None
    assert engine.url is not None


def test_get_session_returns_session():
    """Test that get_session returns a valid session"""
    session_gen = get_session()
    session = next(session_gen)
    assert session is not None
    session.close()


def test_create_tables_creates_all_tables():
    """Test that create_tables creates all required tables"""
    # Create tables
    create_tables()
    
    # Verify tables exist
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    assert "route_watches" in table_names
    assert "price_snapshots" in table_names
    assert "alert_logs" in table_names


def test_base_metadata_has_all_models():
    """Test that Base.metadata contains all model tables"""
    table_names = [table.name for table in Base.metadata.tables.values()]
    
    assert "route_watches" in table_names
    assert "price_snapshots" in table_names
    assert "alert_logs" in table_names
