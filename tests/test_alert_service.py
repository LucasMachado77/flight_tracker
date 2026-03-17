"""Testes para AlertService"""
import pytest
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.route_watch import RouteWatch
from app.models.alert_log import AlertLog
from app.repositories.alert_log_repository import AlertLogRepository
from app.repositories.route_watch_repository import RouteWatchRepository
from app.services.alert_service import AlertService


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
def alert_repo(db_session):
    """Cria um repositório de AlertLog"""
    return AlertLogRepository(db_session)


@pytest.fixture
def alert_service(alert_repo):
    """Cria uma instância de AlertService"""
    return AlertService(alert_repo)


@pytest.fixture
def sample_route(route_watch_repo):
    """Cria uma RouteWatch de exemplo com notificações ativas"""
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


def test_should_alert_returns_false_when_notify_disabled(alert_service, sample_route):
    """Testa que should_alert retorna False quando notify_on_new_low é False"""
    sample_route.notify_on_new_low = False
    
    result = alert_service.should_alert(
        route=sample_route,
        current_price=400.0,
        historical_low=500.0,
    )
    
    assert result is False


def test_should_alert_returns_true_for_first_price(alert_service, sample_route):
    """Testa que should_alert retorna True para o primeiro preço (sem histórico)"""
    result = alert_service.should_alert(
        route=sample_route,
        current_price=450.0,
        historical_low=None,
    )
    
    assert result is True


def test_should_alert_returns_false_when_price_not_lower(alert_service, sample_route):
    """Testa que should_alert retorna False quando preço atual não é menor que histórico"""
    result = alert_service.should_alert(
        route=sample_route,
        current_price=500.0,
        historical_low=450.0,
    )
    
    assert result is False


def test_should_alert_returns_false_when_price_equal(alert_service, sample_route):
    """Testa que should_alert retorna False quando preço atual é igual ao histórico"""
    result = alert_service.should_alert(
        route=sample_route,
        current_price=450.0,
        historical_low=450.0,
    )
    
    assert result is False


def test_should_alert_returns_true_when_price_lower_and_no_restrictions(alert_service, sample_route):
    """Testa que should_alert retorna True quando preço é menor e não há restrições"""
    result = alert_service.should_alert(
        route=sample_route,
        current_price=400.0,
        historical_low=450.0,
    )
    
    assert result is True


def test_should_alert_respects_min_price_difference(alert_service, sample_route):
    """Testa que should_alert respeita margem mínima de diferença"""
    sample_route.min_price_difference = 50.0
    
    # Diferença de 30 (menor que 50) - não deve alertar
    result = alert_service.should_alert(
        route=sample_route,
        current_price=420.0,
        historical_low=450.0,
    )
    assert result is False
    
    # Diferença de 60 (maior que 50) - deve alertar
    result = alert_service.should_alert(
        route=sample_route,
        current_price=390.0,
        historical_low=450.0,
    )
    assert result is True


def test_should_alert_respects_cooldown(alert_service, alert_repo, sample_route):
    """Testa que should_alert respeita período de cooldown"""
    sample_route.alert_cooldown_hours = 24
    
    # Criar um alerta recente (1 hora atrás)
    recent_alert = AlertLog(
        route_watch_id=sample_route.id,
        price_snapshot_id=1,
        alert_type="new_historical_low",
        channel="telegram",
        sent_at=datetime.utcnow() - timedelta(hours=1),
    )
    alert_repo.create(recent_alert)
    
    # Não deve alertar pois está dentro do cooldown
    result = alert_service.should_alert(
        route=sample_route,
        current_price=400.0,
        historical_low=450.0,
    )
    assert result is False


def test_should_alert_allows_after_cooldown_expires(alert_service, alert_repo, sample_route):
    """Testa que should_alert permite alerta após cooldown expirar"""
    sample_route.alert_cooldown_hours = 24
    
    # Criar um alerta antigo (25 horas atrás)
    old_alert = AlertLog(
        route_watch_id=sample_route.id,
        price_snapshot_id=1,
        alert_type="new_historical_low",
        channel="telegram",
        sent_at=datetime.utcnow() - timedelta(hours=25),
    )
    alert_repo.create(old_alert)
    
    # Deve alertar pois cooldown expirou
    result = alert_service.should_alert(
        route=sample_route,
        current_price=400.0,
        historical_low=450.0,
    )
    assert result is True


def test_should_alert_with_no_previous_alerts(alert_service, sample_route):
    """Testa que should_alert funciona quando não há alertas anteriores"""
    sample_route.alert_cooldown_hours = 24
    
    # Deve alertar pois não há alertas anteriores
    result = alert_service.should_alert(
        route=sample_route,
        current_price=400.0,
        historical_low=450.0,
    )
    assert result is True


def test_should_alert_combines_min_difference_and_cooldown(alert_service, alert_repo, sample_route):
    """Testa que should_alert combina margem mínima e cooldown corretamente"""
    sample_route.min_price_difference = 30.0
    sample_route.alert_cooldown_hours = 24
    
    # Criar alerta antigo (fora do cooldown)
    old_alert = AlertLog(
        route_watch_id=sample_route.id,
        price_snapshot_id=1,
        alert_type="new_historical_low",
        channel="telegram",
        sent_at=datetime.utcnow() - timedelta(hours=25),
    )
    alert_repo.create(old_alert)
    
    # Diferença de 20 (menor que 30) - não deve alertar
    result = alert_service.should_alert(
        route=sample_route,
        current_price=430.0,
        historical_low=450.0,
    )
    assert result is False
    
    # Diferença de 40 (maior que 30) e fora do cooldown - deve alertar
    result = alert_service.should_alert(
        route=sample_route,
        current_price=410.0,
        historical_low=450.0,
    )
    assert result is True


def test_should_alert_edge_case_exact_cooldown_boundary(alert_service, alert_repo, sample_route):
    """Testa comportamento no limite exato do cooldown"""
    sample_route.alert_cooldown_hours = 24
    
    # Criar alerta exatamente 24 horas atrás
    boundary_alert = AlertLog(
        route_watch_id=sample_route.id,
        price_snapshot_id=1,
        alert_type="new_historical_low",
        channel="telegram",
        sent_at=datetime.utcnow() - timedelta(hours=24),
    )
    alert_repo.create(boundary_alert)
    
    # Deve alertar pois cooldown expirou (>= 24 horas)
    result = alert_service.should_alert(
        route=sample_route,
        current_price=400.0,
        historical_low=450.0,
    )
    assert result is True


def test_should_alert_edge_case_exact_min_difference(alert_service, sample_route):
    """Testa comportamento no limite exato da margem mínima"""
    sample_route.min_price_difference = 50.0
    
    # Diferença exatamente igual a 50 - não deve alertar (< não >=)
    result = alert_service.should_alert(
        route=sample_route,
        current_price=400.0,
        historical_low=450.0,
    )
    assert result is False
