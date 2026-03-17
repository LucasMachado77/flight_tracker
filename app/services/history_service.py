"""Serviço de gerenciamento de histórico de preços"""
from datetime import datetime
from typing import Optional, List
from app.models.price_snapshot import PriceSnapshot
from app.models.alert_log import AlertLog
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.repositories.alert_log_repository import AlertLogRepository


class HistoryService:
    """Serviço de gerenciamento de histórico de preços"""
    
    def __init__(
        self, 
        snapshot_repo: PriceSnapshotRepository, 
        alert_repo: AlertLogRepository
    ):
        """
        Inicializa o serviço de histórico.
        
        Args:
            snapshot_repo: Repositório de PriceSnapshot
            alert_repo: Repositório de AlertLog
        """
        self.snapshot_repo = snapshot_repo
        self.alert_repo = alert_repo
    
    def save_snapshot(
        self, 
        route_id: int, 
        offer: dict, 
        raw_response: dict
    ) -> PriceSnapshot:
        """
        Salva snapshot de preço.
        
        Args:
            route_id: ID da RouteWatch
            offer: Oferta normalizada contendo price_total, currency, airline, etc.
            raw_response: Resposta bruta do provider
            
        Returns:
            PriceSnapshot criado
        """
        snapshot = PriceSnapshot(
            route_watch_id=route_id,
            provider="serpapi_google_flights",
            searched_at=datetime.utcnow(),
            price_total=offer["price_total"],
            currency=offer["currency"],
            airline=offer.get("airline"),
            airline_code=offer.get("airline_code"),
            departure_at=offer.get("departure_at"),
            return_at=offer.get("return_at"),
            stops=offer.get("stops"),
            offer_hash=offer.get("offer_hash", ""),
            raw_response_json=raw_response,
        )
        return self.snapshot_repo.create(snapshot)
    
    def get_historical_low(self, route_id: int) -> Optional[float]:
        """
        Retorna o menor preço histórico de uma rota.
        
        Args:
            route_id: ID da RouteWatch
            
        Returns:
            Menor preço ou None se não houver histórico
        """
        return self.snapshot_repo.get_min_price(route_id)
    
    def get_route_history(self, route_id: int) -> List[PriceSnapshot]:
        """
        Retorna histórico completo de uma rota.
        
        Args:
            route_id: ID da RouteWatch
            
        Returns:
            Lista de PriceSnapshot ordenada por data descendente
        """
        return self.snapshot_repo.find_by_route(
            route_id, 
            order_by="searched_at", 
            desc=True
        )
    
    def log_alert(
        self, 
        route_id: int, 
        snapshot_id: int, 
        alert_type: str
    ) -> AlertLog:
        """
        Registra envio de alerta.
        
        Args:
            route_id: ID da RouteWatch
            snapshot_id: ID do PriceSnapshot
            alert_type: Tipo do alerta (ex: "new_historical_low")
            
        Returns:
            AlertLog criado
        """
        alert_log = AlertLog(
            route_watch_id=route_id,
            price_snapshot_id=snapshot_id,
            alert_type=alert_type,
            channel="telegram",
            sent_at=datetime.utcnow(),
        )
        return self.alert_repo.create(alert_log)
