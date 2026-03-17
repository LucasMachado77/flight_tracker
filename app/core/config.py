"""Application configuration using pydantic-settings"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./flight_tracker.db",
        description="Database connection URL"
    )
    
    # SerpApi Configuration
    serpapi_api_key: str = Field(
        ...,
        description="SerpApi API key for flight searches"
    )
    serpapi_timeout: float = Field(
        default=30.0,
        description="Timeout for SerpApi requests in seconds"
    )
    
    # Telegram Configuration
    telegram_bot_token: str = Field(
        ...,
        description="Telegram bot token for sending alerts"
    )
    telegram_chat_id: str = Field(
        ...,
        description="Telegram chat ID to send alerts to"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Application Configuration
    app_name: str = Field(
        default="Flight Price Tracker",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )


# Global settings instance
settings = Settings()
