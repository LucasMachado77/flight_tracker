"""Serviço de regras de alerta"""
from datetime import datetime, timedelta
from typing import Optional
from app.repositories.alert_log_repository import AlertLogRepository
from app.models.route_watch import RouteWatch


class AlertService:
    """Serviço de regras de alerta para decisão de envio de notificações"""
    
    def __init__(self, alert_repo: AlertLogRepository):
        """
        Inicializa o serviço de alertas.
        
        Args:
            alert_repo: Repositório de AlertLog para consultar histórico de alertas
        """
        self.alert_repo = alert_repo
    
    def should_alert(
        self,
        route: RouteWatch,
        current_price: float,
        historical_low: Optional[float],
    ) -> bool:
        """
        Determina se deve enviar alerta baseado nas regras de negócio.
        
        Regras aplicadas:
        1. Não alertar se rota não tem notificação ativa (notify_on_new_low)
        2. Primeiro preço sempre é novo mínimo (historical_low is None)
        3. Preço deve ser menor que histórico
        4. Verificar margem mínima se configurada (min_price_difference)
        5. Verificar cooldown se configurado (alert_cooldown_hours)
        
        Args:
            route: RouteWatch sendo verificada
            current_price: Preço atual encontrado
            historical_low: Menor preço histórico anterior (None se não houver histórico)
            
        Returns:
            True se deve alertar, False caso contrário
            
        Validates:
            - Requisito 4.3: Identificação de novo menor preço histórico
            - Requisito 6.2: Bloqueio de alertas dentro do período de cooldown
            - Requisito 6.5: Envio apenas se diferença for maior que margem mínima
        """
        # Regra 1: Não alertar se rota não tem notificação ativa
        if not route.notify_on_new_low:
            return False
        
        # Regra 2: Primeiro preço sempre é novo mínimo
        if historical_low is None:
            return True
        
        # Regra 3: Preço deve ser menor que histórico
        if current_price >= historical_low:
            return False
        
        # Regra 4: Verificar margem mínima se configurada
        if route.min_price_difference is not None:
            price_difference = historical_low - current_price
            if price_difference <= route.min_price_difference:
                return False
        
        # Regra 5: Verificar cooldown se configurado
        if route.alert_cooldown_hours is not None:
            last_alert = self.alert_repo.get_last_alert(route.id)
            if last_alert:
                cooldown_end = last_alert.sent_at + timedelta(hours=route.alert_cooldown_hours)
                if datetime.utcnow() < cooldown_end:
                    return False
        
        return True
