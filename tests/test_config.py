"""Tests for configuration loading"""
import pytest
from pydantic import ValidationError


def test_config_requires_mandatory_fields():
    """Test that Settings validates required fields"""
    from app.core.config import Settings
    
    # Should raise ValidationError when required fields are missing
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,  # Don't load from .env file
            database_url="sqlite:///test.db",
            # Missing serpapi_api_key, telegram_bot_token, telegram_chat_id
        )
    
    # Verify the error mentions the missing fields
    error_str = str(exc_info.value)
    assert "serpapi_api_key" in error_str
    assert "telegram_bot_token" in error_str
    assert "telegram_chat_id" in error_str


def test_config_with_all_required_fields():
    """Test that Settings works with all required fields"""
    from app.core.config import Settings
    
    settings = Settings(
        database_url="sqlite:///test.db",
        serpapi_api_key="test_key",
        telegram_bot_token="test_token",
        telegram_chat_id="test_chat_id",
    )
    
    assert settings.database_url == "sqlite:///test.db"
    assert settings.serpapi_api_key == "test_key"
    assert settings.telegram_bot_token == "test_token"
    assert settings.telegram_chat_id == "test_chat_id"
    assert settings.serpapi_timeout == 30.0  # Default value
    assert settings.log_level == "INFO"  # Default value


def test_config_with_custom_values():
    """Test that Settings accepts custom values for optional fields"""
    from app.core.config import Settings
    
    settings = Settings(
        database_url="postgresql://localhost/test",
        serpapi_api_key="test_key",
        serpapi_timeout=60.0,
        telegram_bot_token="test_token",
        telegram_chat_id="test_chat_id",
        log_level="DEBUG",
        app_name="Test App",
        app_version="2.0.0",
    )
    
    assert settings.database_url == "postgresql://localhost/test"
    assert settings.serpapi_timeout == 60.0
    assert settings.log_level == "DEBUG"
    assert settings.app_name == "Test App"
    assert settings.app_version == "2.0.0"
