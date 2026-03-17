"""Endpoints da API para RouteWatch"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.repositories.route_watch_repository import RouteWatchRepository
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.schemas.route_watch import (
    RouteWatchCreate,
    RouteWatchUpdate,
    RouteWatchResponse,
    PriceSnapshotResponse
)
from app.models.route_watch import RouteWatch
from app.services.flight_search_service import FlightSearchService
from app.services.providers.serpapi_google_flights import SerpApiGoogleFlightsProvider
from app.services.history_service import HistoryService
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.repositories.alert_log_repository import AlertLogRepository
from app.core.config import settings

router = APIRouter(prefix="/route-watches", tags=["route-watches"])


def get_route_watch_repo(session: Session = Depends(get_session)) -> RouteWatchRepository:
    """Dependency para RouteWatchRepository"""
    return RouteWatchRepository(session)


def get_price_snapshot_repo(session: Session = Depends(get_session)) -> PriceSnapshotRepository:
    """Dependency para PriceSnapshotRepository"""
    return PriceSnapshotRepository(session)


def get_alert_log_repo(session: Session = Depends(get_session)) -> AlertLogRepository:
    """Dependency para AlertLogRepository"""
    return AlertLogRepository(session)


def get_flight_search_service(
    session: Session = Depends(get_session)
) -> FlightSearchService:
    """Dependency para FlightSearchService"""
    try:
        # Criar provider
        provider = SerpApiGoogleFlightsProvider(
            api_key=settings.serpapi_api_key,
            timeout=settings.serpapi_timeout
        )
        
        # Criar repositórios
        snapshot_repo = PriceSnapshotRepository(session)
        alert_repo = AlertLogRepository(session)
        
        # Criar serviços
        history_service = HistoryService(snapshot_repo, alert_repo)
        alert_service = AlertService(alert_repo)
        notification_service = NotificationService(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id
        )
        
        return FlightSearchService(
            provider=provider,
            history_service=history_service,
            alert_service=alert_service,
            notification_service=notification_service
        )
    except Exception as e:
        logging.error(f"Erro ao criar FlightSearchService: {e}")
        raise HTTPException(status_code=500, detail="Erro de configuração do serviço")


@router.post("/", response_model=RouteWatchResponse, status_code=201)
def create_route_watch(
    route_data: RouteWatchCreate,
    repo: RouteWatchRepository = Depends(get_route_watch_repo)
) -> RouteWatchResponse:
    """
    Criar nova rota monitorada.
    
    Valida: Requisitos 1.1, 1.2, 1.3, 1.4, 1.5
    """
    route = RouteWatch(
        origin=route_data.origin,
        destination=route_data.destination,
        departure_date=route_data.departure_date,
        return_date=route_data.return_date,
        adults=route_data.adults,
        cabin_class=route_data.cabin_class,
        max_stops=route_data.max_stops,
        currency=route_data.currency,
        check_interval_minutes=route_data.check_interval_minutes,
        notify_on_new_low=route_data.notify_on_new_low,
        target_price=route_data.target_price,
        min_price_difference=route_data.min_price_difference,
        alert_cooldown_hours=route_data.alert_cooldown_hours,
        flexible_dates=route_data.flexible_dates,
    )
    
    created_route = repo.create(route)
    return RouteWatchResponse.model_validate(created_route)


@router.get("/", response_model=List[RouteWatchResponse])
def list_route_watches(
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo/inativo"),
    repo: RouteWatchRepository = Depends(get_route_watch_repo)
) -> List[RouteWatchResponse]:
    """
    Listar rotas monitoradas com filtro opcional por status.
    
    Valida: Requisitos 9.1, 9.2, 9.4
    """
    try:
        if is_active is not None:
            routes = repo.find_by_status(is_active)
        else:
            routes = repo.find_all()
        
        return [RouteWatchResponse.model_validate(route) for route in routes]
    except Exception as e:
        logging.error(f"Erro ao listar rotas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao listar rotas")


@router.get("/{route_id}", response_model=RouteWatchResponse)
def get_route_watch(
    route_id: int,
    repo: RouteWatchRepository = Depends(get_route_watch_repo)
) -> RouteWatchResponse:
    """
    Obter rota específica por ID.
    
    Valida: Requisitos 9.1
    """
    route = repo.find_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="RouteWatch não encontrada")
    
    return RouteWatchResponse.model_validate(route)


@router.patch("/{route_id}", response_model=RouteWatchResponse)
def update_route_watch(
    route_id: int,
    update_data: RouteWatchUpdate,
    repo: RouteWatchRepository = Depends(get_route_watch_repo)
) -> RouteWatchResponse:
    """
    Atualizar rota monitorada (ativar/desativar e outras configurações).
    
    Valida: Requisitos 11.1, 11.4
    """
    route = repo.find_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="RouteWatch não encontrada")
    
    # Atualizar apenas campos fornecidos
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(route, field, value)
    
    updated_route = repo.update(route)
    return RouteWatchResponse.model_validate(updated_route)


@router.get("/{route_id}/history", response_model=List[PriceSnapshotResponse])
def get_route_history(
    route_id: int,
    repo: RouteWatchRepository = Depends(get_route_watch_repo),
    snapshot_repo: PriceSnapshotRepository = Depends(get_price_snapshot_repo)
) -> List[PriceSnapshotResponse]:
    """
    Consultar histórico de preços de uma rota.
    
    Valida: Requisitos 10.1, 10.2, 10.3
    """
    # Verificar se rota existe
    route = repo.find_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="RouteWatch não encontrada")
    
    # Buscar histórico
    snapshots = snapshot_repo.find_by_route(
        route_id, order_by="searched_at", desc=True
    )

    # Comentário (pt-BR): adiciona informações de passageiros e preço por passageiro em cada item do histórico
    history_responses: List[PriceSnapshotResponse] = []
    passengers = route.adults

    for snapshot in snapshots:
        price_per_passenger = (
            snapshot.price_total / passengers if passengers else None
        )

        history_responses.append(
            PriceSnapshotResponse(
                id=snapshot.id,
                route_watch_id=snapshot.route_watch_id,
                provider=snapshot.provider,
                searched_at=snapshot.searched_at,
                price_total=snapshot.price_total,
                currency=snapshot.currency,
                airline=snapshot.airline,
                airline_code=snapshot.airline_code,
                departure_at=snapshot.departure_at,
                return_at=snapshot.return_at,
                stops=snapshot.stops,
                offer_hash=snapshot.offer_hash,
                passengers=passengers,
                price_per_passenger=price_per_passenger,
            )
        )

    return history_responses


@router.post("/{route_id}/check", response_model=dict)
def check_route_price(
    route_id: int,
    repo: RouteWatchRepository = Depends(get_route_watch_repo),
    snapshot_repo: PriceSnapshotRepository = Depends(get_price_snapshot_repo),
    flight_service: FlightSearchService = Depends(get_flight_search_service)
) -> dict:
    """
    Mostrar último preço salvo ou disparar consulta manual se não houver histórico.
    
    Valida: Requisitos 8.1, 8.2
    """
    try:
        # Log estruturado para facilitar debug de chamadas manuais
        logging.info(f"Verificação manual de preço solicitada para rota {route_id}")

        # Verificar se rota existe
        route = repo.find_by_id(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="RouteWatch não encontrada")

        # Buscar último snapshot salvo
        last_snapshots = snapshot_repo.find_by_route(
            route_id, order_by="searched_at", desc=True
        )

        # Se há histórico, retornar último preço salvo
        if last_snapshots:
            last_snapshot = last_snapshots[0]

            # Usar conversão segura para tipos de data/hora, aceitando tanto str quanto datetime
            def _to_iso(value):
                # Comentário (pt-BR): converte datetime para string ISO sem quebrar se já for string ou None
                if value is None:
                    return None
                if hasattr(value, "isoformat"):
                    return value.isoformat()
                return str(value)

            passengers = route.adults
            price_per_passenger = (
                last_snapshot.price_total / passengers if passengers else None
            )

            return {
                "success": True,
                "message": "Último preço encontrado no histórico",
                "snapshot_id": last_snapshot.id,
                "price_total": last_snapshot.price_total,
                "currency": last_snapshot.currency,
                "searched_at": _to_iso(last_snapshot.searched_at),
                "airline": last_snapshot.airline,
                "departure_at": _to_iso(last_snapshot.departure_at),
                "return_at": _to_iso(last_snapshot.return_at),
                "passengers": passengers,
                "price_per_passenger": price_per_passenger,
                "from_cache": True,
            }

        # Se não há histórico, fazer nova consulta usando o serviço
        snapshot = flight_service.check_route_price(route)

        if snapshot:
            def _to_iso(value):
                # Comentário (pt-BR): mesma função auxiliar para garantir formato seguro nas respostas
                if value is None:
                    return None
                if hasattr(value, "isoformat"):
                    return value.isoformat()
                return str(value)

            passengers = route.adults
            price_per_passenger = (
                snapshot.price_total / passengers if passengers else None
            )

            return {
                "success": True,
                "message": "Nova consulta executada com sucesso",
                "snapshot_id": snapshot.id,
                "price_total": snapshot.price_total,
                "currency": snapshot.currency,
                "searched_at": _to_iso(snapshot.searched_at),
                "airline": snapshot.airline,
                "departure_at": _to_iso(snapshot.departure_at),
                "return_at": _to_iso(snapshot.return_at),
                 "passengers": passengers,
                 "price_per_passenger": price_per_passenger,
                "from_cache": False,
            }

        # Caso o serviço não consiga obter um snapshot
        return {
            "success": False,
            "message": "Falha na consulta - verifique logs para detalhes",
        }
    except HTTPException:
        # Repassa erros HTTP explícitos (404, etc.)
        raise
    except Exception as e:
        # Log detalhado de qualquer outro erro inesperado
        logging.error(
            f"Erro interno ao verificar preço da rota {route_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")