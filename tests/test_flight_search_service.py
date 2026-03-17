"""Testes para FlightSearchService"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.route_watch import RouteWatch
from app.models.price_snapshot import PriceSnapshot
from app.repositories.route_watch_repository import RouteWatchRepository
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.repositories.alert_log_repository import AlertLogRepository
from app.services.flight_search_service import FlightSearchService
from app.services.history_service import HistoryService
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService


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
def alert_service(alert_repo):
    """Cria uma instância de AlertService"""
    return AlertService(alert_repo)


@pytest.fixture
def mock_provider():
    """Cria um mock do FlightProvider"""
    provider = Mock()
    return provider


@pytest.fixture
def mock_notification_service():
    """Cria um mock do NotificationService"""
    notification = Mock()
    notification.send_new_low_alert = Mock(return_value=True)
    return notification


@pytest.fixture
def flight_search_service(
    mock_provider, history_service, alert_service, mock_notification_service
):
    """Cria uma instância de FlightSearchService"""
    return FlightSearchService(
        provider=mock_provider,
        history_service=history_service,
        alert_service=alert_service,
        notification_service=mock_notification_service,
    )


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
        notify_on_new_low=True,
        is_active=True,
    )
    return route_watch_repo.create(route)


def test_check_route_price_creates_snapshot(
    flight_search_service, mock_provider, sample_route
):
    """Testa que check_route_price cria um snapshot quando há ofertas"""
    # Configurar mock do provider
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [
                {
                    "price_total": 450.0,
                    "currency": "EUR",
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_at": "10:30",
                    "return_at": "14:45",
                    "stops": 0,
                    "offer_hash": "abc123",
                }
            ],
            "raw_response": {"test": "data"},
        }
    )
    
    snapshot = flight_search_service.check_route_price(sample_route)
    
    assert snapshot is not None
    assert snapshot.route_watch_id == sample_route.id
    assert snapshot.price_total == 450.0
    assert snapshot.currency == "EUR"


def test_check_route_price_calls_provider_with_correct_params(
    flight_search_service, mock_provider, sample_route
):
    """Testa que check_route_price chama o provider com parâmetros corretos"""
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [{"price_total": 450.0, "currency": "EUR"}],
            "raw_response": {"test": "data"},
        }
    )
    
    flight_search_service.check_route_price(sample_route)
    
    mock_provider.search_flights.assert_called_once_with(
        origin="LIS",
        destination="GRU",
        departure_date="2026-07-15",
        return_date="2026-07-25",
        adults=1,
        cabin_class="ECONOMY",
        currency="EUR",
    )


def test_check_route_price_returns_none_when_no_offers(
    flight_search_service, mock_provider, sample_route
):
    """Testa que check_route_price retorna None quando não há ofertas"""
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [],
            "raw_response": {"test": "data"},
        }
    )
    
    snapshot = flight_search_service.check_route_price(sample_route)
    
    assert snapshot is None


def test_check_route_price_selects_cheapest_offer(
    flight_search_service, mock_provider, sample_route
):
    """Testa que check_route_price seleciona a oferta mais barata"""
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [
                {"price_total": 500.0, "currency": "EUR"},
                {"price_total": 450.0, "currency": "EUR"},
                {"price_total": 480.0, "currency": "EUR"},
            ],
            "raw_response": {"test": "data"},
        }
    )
    
    snapshot = flight_search_service.check_route_price(sample_route)
    
    assert snapshot.price_total == 450.0


def test_check_route_price_sends_alert_for_new_low(
    flight_search_service, mock_provider, mock_notification_service, sample_route
):
    """Testa que check_route_price envia alerta para novo menor preço"""
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [
                {
                    "price_total": 450.0,
                    "currency": "EUR",
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_at": "10:30",
                    "return_at": "14:45",
                    "stops": 0,
                    "offer_hash": "abc123",
                }
            ],
            "raw_response": {"test": "data"},
        }
    )
    
    flight_search_service.check_route_price(sample_route)
    
    # Deve enviar alerta pois é o primeiro preço (novo mínimo)
    mock_notification_service.send_new_low_alert.assert_called_once()


def test_check_route_price_does_not_alert_for_higher_price(
    flight_search_service, mock_provider, mock_notification_service, sample_route
):
    """Testa que check_route_price não envia alerta para preço maior"""
    # Primeiro, criar um snapshot com preço baixo
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [
                {
                    "price_total": 400.0,
                    "currency": "EUR",
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_at": "10:30",
                    "return_at": "14:45",
                    "stops": 0,
                    "offer_hash": "abc123",
                }
            ],
            "raw_response": {"test": "data"},
        }
    )
    
    flight_search_service.check_route_price(sample_route)
    mock_notification_service.send_new_low_alert.reset_mock()
    
    # Agora, consultar com preço maior
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [
                {
                    "price_total": 500.0,
                    "currency": "EUR",
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_at": "10:30",
                    "return_at": "14:45",
                    "stops": 0,
                    "offer_hash": "abc123",
                }
            ],
            "raw_response": {"test": "data"},
        }
    )
    
    flight_search_service.check_route_price(sample_route)
    
    # Não deve enviar alerta pois o preço é maior
    mock_notification_service.send_new_low_alert.assert_not_called()


def test_check_route_price_returns_none_on_provider_error(
    flight_search_service, mock_provider, sample_route
):
    """Testa que check_route_price retorna None quando o provider falha"""
    mock_provider.search_flights = Mock(side_effect=Exception("Provider error"))
    
    snapshot = flight_search_service.check_route_price(sample_route)
    
    assert snapshot is None


def test_check_route_price_continues_after_notification_error(
    flight_search_service, mock_provider, mock_notification_service, sample_route
):
    """Testa que check_route_price continua mesmo se notificação falhar"""
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [
                {
                    "price_total": 450.0,
                    "currency": "EUR",
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_at": "10:30",
                    "return_at": "14:45",
                    "stops": 0,
                    "offer_hash": "abc123",
                }
            ],
            "raw_response": {"test": "data"},
        }
    )
    
    # Simular erro na notificação
    mock_notification_service.send_new_low_alert = Mock(
        side_effect=Exception("Notification error")
    )
    
    # Deve criar snapshot mesmo com erro na notificação
    snapshot = flight_search_service.check_route_price(sample_route)
    
    assert snapshot is not None
    assert snapshot.price_total == 450.0


def test_check_route_price_logs_alert_when_sent(
    flight_search_service, mock_provider, alert_repo, sample_route
):
    """Testa que check_route_price registra AlertLog quando alerta é enviado"""
    mock_provider.search_flights = Mock(return_value={"test": "data"})
    mock_provider.normalize_response = Mock(
        return_value={
            "provider": "serpapi_google_flights",
            "offers": [
                {
                    "price_total": 450.0,
                    "currency": "EUR",
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_at": "10:30",
                    "return_at": "14:45",
                    "stops": 0,
                    "offer_hash": "abc123",
                }
            ],
            "raw_response": {"test": "data"},
        }
    )
    
    snapshot = flight_search_service.check_route_price(sample_route)
    
    # Verificar que AlertLog foi criado
    last_alert = alert_repo.get_last_alert(sample_route.id)
    assert last_alert is not None
    assert last_alert.route_watch_id == sample_route.id
    assert last_alert.price_snapshot_id == snapshot.id
    assert last_alert.alert_type == "new_historical_low"

