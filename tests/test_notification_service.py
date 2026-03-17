"""Testes para NotificationService"""
import pytest
from datetime import date
from unittest.mock import Mock, patch
from app.services.notification_service import NotificationService
from app.models.route_watch import RouteWatch


@pytest.fixture
def notification_service():
    """Cria uma instância de NotificationService"""
    return NotificationService(
        bot_token="test_bot_token_123",
        chat_id="test_chat_id_456"
    )


@pytest.fixture
def sample_route():
    """Cria uma RouteWatch de exemplo"""
    route = Mock(spec=RouteWatch)
    route.id = 1
    route.origin = "LIS"
    route.destination = "GRU"
    route.departure_date = date(2026, 7, 15)
    route.return_date = date(2026, 7, 25)
    route.currency = "EUR"
    return route


@pytest.fixture
def sample_offer_details():
    """Cria detalhes de oferta de exemplo"""
    return {
        "airline": "TAP Air Portugal",
        "stops": 0,
        "departure_at": "2026-07-15 10:30",
        "return_at": "2026-07-25 14:45",
    }


def test_notification_service_initialization(notification_service):
    """Testa inicialização do NotificationService"""
    assert notification_service.bot_token == "test_bot_token_123"
    assert notification_service.chat_id == "test_chat_id_456"
    assert notification_service.base_url == "https://api.telegram.org/bottest_bot_token_123"


def test_format_alert_message_with_historical_low(notification_service, sample_route, sample_offer_details):
    """Testa formatação de mensagem com menor preço anterior"""
    message = notification_service._format_alert_message(
        route=sample_route,
        current_price=450.50,
        historical_low=500.00,
        offer_details=sample_offer_details,
    )
    
    assert "🔥" in message
    assert "Novo menor preço histórico!" in message
    assert "LIS → GRU" in message
    assert "15/07/2026" in message
    assert "25/07/2026" in message
    assert "TAP Air Portugal" in message
    assert "EUR 450.50" in message
    assert "EUR 500.00" in message
    assert "0" in message  # stops
    assert "2026-07-15 10:30" in message
    assert "2026-07-25 14:45" in message
    assert "SerpApi / Google Flights" in message


def test_format_alert_message_without_historical_low(notification_service, sample_route, sample_offer_details):
    """Testa formatação de mensagem sem menor preço anterior (primeiro preço)"""
    message = notification_service._format_alert_message(
        route=sample_route,
        current_price=450.50,
        historical_low=None,
        offer_details=sample_offer_details,
    )
    
    assert "Novo menor preço histórico!" in message
    assert "EUR 450.50" in message
    assert "EUR N/A" in message


def test_format_alert_message_with_stops(notification_service, sample_route):
    """Testa formatação de mensagem com escalas"""
    offer_details = {
        "airline": "Lufthansa",
        "stops": 2,
        "departure_at": "2026-07-15 08:00",
        "return_at": "2026-07-25 20:00",
    }
    
    message = notification_service._format_alert_message(
        route=sample_route,
        current_price=350.00,
        historical_low=400.00,
        offer_details=offer_details,
    )
    
    assert "Lufthansa" in message
    assert "2" in message  # stops


@patch('httpx.post')
def test_send_new_low_alert_success(mock_post, notification_service, sample_route, sample_offer_details):
    """Testa envio bem-sucedido de alerta"""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    result = notification_service.send_new_low_alert(
        route=sample_route,
        current_price=450.50,
        historical_low=500.00,
        offer_details=sample_offer_details,
    )
    
    assert result is True
    mock_post.assert_called_once()
    
    # Verificar argumentos da chamada
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://api.telegram.org/bottest_bot_token_123/sendMessage"
    assert call_args[1]["json"]["chat_id"] == "test_chat_id_456"
    assert call_args[1]["json"]["parse_mode"] == "HTML"
    assert "Novo menor preço histórico!" in call_args[1]["json"]["text"]
    assert call_args[1]["timeout"] == 10.0


@patch('httpx.post')
def test_send_new_low_alert_http_error(mock_post, notification_service, sample_route, sample_offer_details):
    """Testa tratamento de erro HTTP ao enviar alerta"""
    mock_post.side_effect = Exception("Network error")
    
    result = notification_service.send_new_low_alert(
        route=sample_route,
        current_price=450.50,
        historical_low=500.00,
        offer_details=sample_offer_details,
    )
    
    assert result is False


@patch('httpx.post')
def test_send_new_low_alert_logs_error(mock_post, notification_service, sample_route, sample_offer_details, caplog):
    """Testa que erros são registrados em log"""
    import logging
    caplog.set_level(logging.ERROR)
    
    mock_post.side_effect = Exception("Connection timeout")
    
    notification_service.send_new_low_alert(
        route=sample_route,
        current_price=450.50,
        historical_low=500.00,
        offer_details=sample_offer_details,
    )
    
    assert "Erro ao enviar alerta via Telegram" in caplog.text
    assert "Connection timeout" in caplog.text


@patch('httpx.post')
def test_send_new_low_alert_logs_success(mock_post, notification_service, sample_route, sample_offer_details, caplog):
    """Testa que sucesso é registrado em log"""
    import logging
    caplog.set_level(logging.INFO)
    
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    notification_service.send_new_low_alert(
        route=sample_route,
        current_price=450.50,
        historical_low=500.00,
        offer_details=sample_offer_details,
    )
    
    assert "Alerta enviado via Telegram para RouteWatch 1" in caplog.text


def test_format_alert_message_decimal_precision(notification_service, sample_route, sample_offer_details):
    """Testa formatação de preços com precisão decimal"""
    message = notification_service._format_alert_message(
        route=sample_route,
        current_price=123.456,
        historical_low=234.567,
        offer_details=sample_offer_details,
    )
    
    # Deve formatar com 2 casas decimais
    assert "EUR 123.46" in message
    assert "EUR 234.57" in message
