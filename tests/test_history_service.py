"""Testes para HistoryService"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.route_watch import RouteWatch
from app.models.price_snapshot import PriceSnapshot
from app.models.alert_log import AlertLog
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.repositories.alert_log_repository import AlertLogRepository
from app.repositories.route_watch_repository import RouteWatchRepository
from app.services.history_service import HistoryService
from datetime import date


@pytest.fixture
def db_session():
    """Cria uma sessão de banco de dados em memória para testes"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def route_watch_repo(db_session):
    """Cria um repositório de RouteWatch"""
    return RouteWatchRepository(db_session)


@pytest.fixture
def snapshot_repo(db_session):
    """Cria um repositório de PriceSnapshot"""
    return PriceSnapshotRepository(db_session)


@pytest.fixture
def alert_repo(db_session):
    """Cria um repositório de AlertLog"""
    return AlertLogRepository(db_session)


@pytest.fixture
def history_service(snapshot_repo, alert_repo):
    """Cria uma instância de HistoryService"""
    return HistoryService(snapshot_repo, alert_repo)


@pytest.fixture
def sample_route(route_watch_repo):
    """Cria uma RouteWatch de exemplo"""
    route = RouteWatch(
        origin="LIS",
        destination="GRU",
        departure_date=date(2026, 7, 15),
        return_date=date(2026, 7, 25),
        adults=1,
        cabin_class="ECONOMY",
        currency="EUR",
        check_interval_minutes=360,
        is_active=True,
    )
    return route_watch_repo.create(route)


def test_save_snapshot_creates_snapshot(history_service, sample_route):
    """Testa que save_snapshot cria um PriceSnapshot com todos os campos"""
    offer = {
        "price_total": 450.50,
        "currency": "EUR",
        "airline": "TAP Air Portugal",
        "airline_code": "TP",
        "departure_at": "2026-07-15 10:30",
        "return_at": "2026-07-25 14:45",
        "stops": 0,
        "offer_hash": "abc123",
    }
    raw_response = {"test": "data"}
    
    snapshot = history_service.save_snapshot(
        route_id=sample_route.id,
        offer=offer,
        raw_response=raw_response,
    )
    
    assert snapshot.id is not None
    assert snapshot.route_watch_id == sample_route.id
    assert snapshot.provider == "serpapi_google_flights"
    assert snapshot.price_total == 450.50
    assert snapshot.currency == "EUR"
    assert snapshot.airline == "TAP Air Portugal"
    assert snapshot.airline_code == "TP"
    assert snapshot.departure_at == "2026-07-15 10:30"
    assert snapshot.return_at == "2026-07-25 14:45"
    assert snapshot.stops == 0
    assert snapshot.offer_hash == "abc123"
    assert snapshot.raw_response_json == {"test": "data"}
    assert snapshot.searched_at is not None


def test_get_historical_low_returns_none_when_no_snapshots(history_service, sample_route):
    """Testa que get_historical_low retorna None quando não há snapshots"""
    result = history_service.get_historical_low(sample_route.id)
    assert result is None


def test_get_historical_low_returns_minimum_price(history_service, sample_route):
    """Testa que get_historical_low retorna o menor preço"""
    offers = [
        {"price_total": 500.0, "currency": "EUR"},
        {"price_total": 450.0, "currency": "EUR"},
        {"price_total": 480.0, "currency": "EUR"},
    ]
    
    for offer in offers:
        history_service.save_snapshot(
            route_id=sample_route.id,
            offer=offer,
            raw_response={},
        )
    
    result = history_service.get_historical_low(sample_route.id)
    assert result == 450.0


def test_get_route_history_returns_all_snapshots(history_service, sample_route):
    """Testa que get_route_history retorna todos os snapshots"""
    offers = [
        {"price_total": 500.0, "currency": "EUR"},
        {"price_total": 450.0, "currency": "EUR"},
        {"price_total": 480.0, "currency": "EUR"},
    ]
    
    for offer in offers:
        history_service.save_snapshot(
            route_id=sample_route.id,
            offer=offer,
            raw_response={},
        )
    
    history = history_service.get_route_history(sample_route.id)
    assert len(history) == 3
    assert all(isinstance(s, PriceSnapshot) for s in history)


def test_get_route_history_ordered_by_date_desc(history_service, sample_route):
    """Testa que get_route_history retorna snapshots ordenados por data descendente"""
    history = history_service.get_route_history(sample_route.id)
    
    if len(history) > 1:
        for i in range(len(history) - 1):
            assert history[i].searched_at >= history[i + 1].searched_at


def test_log_alert_creates_alert_log(history_service, sample_route):
    """Testa que log_alert cria um AlertLog"""
    offer = {"price_total": 450.0, "currency": "EUR"}
    snapshot = history_service.save_snapshot(
        route_id=sample_route.id,
        offer=offer,
        raw_response={},
    )
    
    alert_log = history_service.log_alert(
        route_id=sample_route.id,
        snapshot_id=snapshot.id,
        alert_type="new_historical_low",
    )
    
    assert alert_log.id is not None
    assert alert_log.route_watch_id == sample_route.id
    assert alert_log.price_snapshot_id == snapshot.id
    assert alert_log.alert_type == "new_historical_low"
    assert alert_log.channel == "telegram"
    assert alert_log.sent_at is not None


def test_get_route_history_returns_empty_list_when_no_snapshots(history_service, sample_route):
    """Testa que get_route_history retorna lista vazia quando não há snapshots"""
    history = history_service.get_route_history(sample_route.id)
    assert history == []
