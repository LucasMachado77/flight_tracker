"""Schemas Pydantic para RouteWatch"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class RouteWatchCreate(BaseModel):
    """Schema para criação de RouteWatch"""
    origin: str = Field(..., min_length=3, max_length=3, description="Código IATA do aeroporto de origem")
    destination: str = Field(..., min_length=3, max_length=3, description="Código IATA do aeroporto de destino")
    departure_date: date = Field(..., description="Data de ida")
    return_date: date = Field(..., description="Data de volta")
    adults: int = Field(default=1, ge=1, le=9, description="Número de passageiros adultos")
    cabin_class: str = Field(default="ECONOMY", description="Classe da cabine")
    max_stops: Optional[int] = Field(default=None, ge=0, description="Número máximo de escalas")
    currency: str = Field(default="EUR", min_length=3, max_length=3, description="Código da moeda")
    check_interval_minutes: int = Field(default=360, ge=60, description="Intervalo de verificação em minutos")
    notify_on_new_low: bool = Field(default=True, description="Notificar sobre novos menores preços")
    target_price: Optional[float] = Field(default=None, gt=0, description="Preço alvo")
    min_price_difference: Optional[float] = Field(default=None, gt=0, description="Diferença mínima para alerta")
    alert_cooldown_hours: Optional[int] = Field(default=None, ge=1, description="Cooldown entre alertas em horas")
    flexible_dates: bool = Field(default=True, description="Datas flexíveis (True) ou exatas (False)")

    @validator('departure_date', 'return_date')
    def validate_dates_not_past(cls, v):
        """Valida que as datas não são no passado"""
        from datetime import date as date_today
        if v < date_today.today():
            raise ValueError('Data não pode ser no passado')
        return v

    @validator('return_date')
    def validate_return_after_departure(cls, v, values):
        """Valida que data de volta é após data de ida"""
        if 'departure_date' in values and v <= values['departure_date']:
            raise ValueError('Data de volta deve ser posterior à data de ida')
        return v

    @validator('cabin_class')
    def validate_cabin_class(cls, v):
        """Valida classe da cabine"""
        valid_classes = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST']
        if v not in valid_classes:
            raise ValueError(f'Classe deve ser uma de: {", ".join(valid_classes)}')
        return v

    @validator('origin', 'destination')
    def validate_iata_codes(cls, v):
        """Valida códigos IATA"""
        if not v.isupper():
            raise ValueError('Código IATA deve estar em maiúsculas')
        return v


class RouteWatchUpdate(BaseModel):
    """Schema para atualização de RouteWatch"""
    departure_date: Optional[date] = Field(default=None, description="Data de ida")
    return_date: Optional[date] = Field(default=None, description="Data de volta")
    is_active: Optional[bool] = Field(default=None, description="Status ativo/inativo")
    adults: Optional[int] = Field(default=None, ge=1, le=9, description="Número de passageiros adultos")
    cabin_class: Optional[str] = Field(default=None, description="Classe da cabine")
    max_stops: Optional[int] = Field(default=None, ge=0, description="Número máximo de escalas")
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3, description="Código da moeda")
    check_interval_minutes: Optional[int] = Field(default=None, ge=60, description="Intervalo de verificação em minutos")
    notify_on_new_low: Optional[bool] = Field(default=None, description="Notificar sobre novos menores preços")
    target_price: Optional[float] = Field(default=None, gt=0, description="Preço alvo")
    min_price_difference: Optional[float] = Field(default=None, gt=0, description="Diferença mínima para alerta")
    alert_cooldown_hours: Optional[int] = Field(default=None, ge=1, description="Cooldown entre alertas em horas")
    flexible_dates: Optional[bool] = Field(default=None, description="Datas flexíveis (True) ou exatas (False)")

    @validator('departure_date', 'return_date')
    def validate_dates_not_past(cls, v):
        """Valida que as datas não são no passado"""
        if v is None:
            return v
        from datetime import date as date_today
        if v < date_today.today():
            raise ValueError('Data não pode ser no passado')
        return v

    @validator('return_date')
    def validate_return_after_departure(cls, v, values):
        """Valida que data de volta é após data de ida"""
        if v is None or 'departure_date' not in values or values['departure_date'] is None:
            return v
        if v <= values['departure_date']:
            raise ValueError('Data de volta deve ser posterior à data de ida')
        return v

    @validator('cabin_class')
    def validate_cabin_class(cls, v):
        """Valida classe da cabine"""
        if v is None:
            return v
        valid_classes = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST']
        if v not in valid_classes:
            raise ValueError(f'Classe deve ser uma de: {", ".join(valid_classes)}')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        """Valida código da moeda"""
        if v is None:
            return v
        if not v.isupper():
            raise ValueError('Código da moeda deve estar em maiúsculas')
        return v


class RouteWatchResponse(BaseModel):
    """Schema para resposta de RouteWatch"""
    id: int
    origin: str
    destination: str
    departure_date: date
    return_date: date
    adults: int
    cabin_class: str
    max_stops: Optional[int]
    currency: str
    check_interval_minutes: int
    notify_on_new_low: bool
    target_price: Optional[float]
    min_price_difference: Optional[float]
    alert_cooldown_hours: Optional[int]
    is_active: bool
    flexible_dates: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PriceSnapshotResponse(BaseModel):
    """Schema para resposta de PriceSnapshot"""
    id: int
    route_watch_id: int
    provider: str
    searched_at: datetime
    price_total: float
    currency: str
    airline: Optional[str]
    airline_code: Optional[str]
    departure_at: Optional[datetime]
    return_at: Optional[datetime]
    stops: Optional[int]
    offer_hash: Optional[str]
    passengers: Optional[int] = None
    price_per_passenger: Optional[float] = None

    class Config:
        from_attributes = True