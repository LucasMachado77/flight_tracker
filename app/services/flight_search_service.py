"""Serviço de busca e análise de preços de voos.

Este módulo coordena o processo completo de verificação de preços:
1. Consulta ao provider (SerpApi)
2. Normalização da resposta
3. Seleção da melhor oferta
4. Salvamento do snapshot
5. Verificação de regras de alerta
6. Envio de notificação se aplicável

Valida: Requisitos 2.1, 2.3, 2.4, 4.1, 5.1, 12.5
"""

import logging
from typing import Optional
from app.services.providers.base import FlightProvider
from app.services.history_service import HistoryService
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.models.route_watch import RouteWatch
from app.models.price_snapshot import PriceSnapshot


class FlightSearchService:
    """Serviço de busca e análise de preços de voos.
    
    Coordena o fluxo completo de verificação de preço para uma rota,
    integrando provider, histórico, alertas e notificações.
    
    Attributes:
        provider: Provider de dados de voos (ex: SerpApi)
        history_service: Serviço de gerenciamento de histórico
        alert_service: Serviço de regras de alerta
        notification_service: Serviço de envio de notificações
        logger: Logger para registro de eventos
    """
    
    def __init__(
        self,
        provider: FlightProvider,
        history_service: HistoryService,
        alert_service: AlertService,
        notification_service: NotificationService,
    ):
        """Inicializa o serviço de busca de voos.
        
        Args:
            provider: Provider de dados de voos
            history_service: Serviço de histórico
            alert_service: Serviço de alertas
            notification_service: Serviço de notificações
        """
        self.provider = provider
        self.history_service = history_service
        self.alert_service = alert_service
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)
    
    def check_route_price(self, route: RouteWatch) -> Optional[PriceSnapshot]:
        """Executa verificação completa de preço para uma rota.
        
        Fluxo de execução:
        1. Log início da consulta
        2. Consultar provider para obter preços
        3. Normalizar resposta do provider
        4. Selecionar melhor oferta (menor preço)
        5. Buscar menor preço histórico
        6. Salvar snapshot do preço atual
        7. Verificar se deve enviar alerta
        8. Enviar notificação se aplicável
        9. Registrar alerta no histórico
        
        Args:
            route: RouteWatch a ser verificada
            
        Returns:
            PriceSnapshot criado ou None se falhar
            
        Valida:
            - Requisito 2.1: Execução de consultas para RouteWatch ativas
            - Requisito 2.3: Logging de início e conclusão
            - Requisito 2.4: Continuidade após falha
            - Requisito 4.1: Consulta de menor preço histórico
            - Requisito 5.1: Envio de alerta para novo menor preço
            - Requisito 12.5: Continuidade após erro
        """
        try:
            # Log início da consulta (Requisito 2.3)
            self.logger.info(f"Iniciando consulta para RouteWatch {route.id}")
            
            # Consultar provider (Requisito 2.1)
            raw_response = self.provider.search_flights(
                origin=route.origin,
                destination=route.destination,
                departure_date=str(route.departure_date),
                return_date=str(route.return_date),
                adults=route.adults,
                cabin_class=route.cabin_class,
                currency=route.currency,
            )
            
            # Normalizar resposta
            normalized = self.provider.normalize_response(raw_response)
            offers = normalized["offers"]
            
            # Verificar se há ofertas (Requisito 12.4)
            if not offers:
                self.logger.warning(
                    f"Nenhuma oferta encontrada para RouteWatch {route.id}"
                )
                return None
            
            # Selecionar melhor oferta (menor preço) (Requisito 7.4)
            best_offer = min(offers, key=lambda x: x["price_total"])
            
            # Log da janela vs resultado baseado no modo
            if route.flexible_dates:
                self.logger.info(
                    f"RouteWatch {route.id} (FLEXÍVEL): Janela {route.departure_date} até {route.return_date}, "
                    f"melhor combinação: {best_offer.get('departure_at', 'N/A')} até {best_offer.get('return_at', 'N/A')}"
                )
            else:
                # Modo exato - validar se as datas correspondem
                date_warning = self._validate_exact_dates(route, best_offer)
                if date_warning:
                    self.logger.warning(f"RouteWatch {route.id} (EXATO): {date_warning}")
                else:
                    self.logger.info(f"RouteWatch {route.id} (EXATO): Voos encontrados nas datas exatas")
            
            # Buscar menor histórico (Requisito 4.1)
            historical_low = self.history_service.get_historical_low(route.id)
            
            # Salvar snapshot (Requisito 3.1)
            snapshot = self.history_service.save_snapshot(
                route_id=route.id,
                offer=best_offer,
                raw_response=raw_response,
            )
            
            # Log snapshot salvo (Requisito 14.1)
            mode_text = "FLEXÍVEL" if route.flexible_dates else "EXATO"
            self.logger.info(
                f"Snapshot salvo: {snapshot.id}, preço: {snapshot.price_total} - "
                f"Modo {mode_text}"
            )
            
            # Verificar se deve alertar (Requisito 4.3, 6.2, 6.5)
            if self.alert_service.should_alert(
                route, best_offer["price_total"], historical_low
            ):
                try:
                    # Enviar notificação (Requisito 5.1)
                    self.notification_service.send_new_low_alert(
                        route=route,
                        current_price=best_offer["price_total"],
                        historical_low=historical_low,
                        offer_details=best_offer,
                    )
                    
                    # Registrar alerta (Requisito 5.3)
                    self.history_service.log_alert(
                        route.id, snapshot.id, "new_historical_low"
                    )
                    
                    # Log alerta enviado (Requisito 14.1)
                    self.logger.info(f"Alerta enviado para RouteWatch {route.id}")
                except Exception as e:
                    # Log erro mas continua (Requisito 5.5)
                    self.logger.error(
                        f"Erro ao enviar alerta para RouteWatch {route.id}: {e}",
                        exc_info=True
                    )
            
            # Log conclusão (Requisito 2.3)
            self.logger.info(f"Consulta concluída para RouteWatch {route.id}")
            
            return snapshot
            
        except Exception as e:
            # Tratamento de erro com continuidade (Requisito 2.4, 12.5)
            self.logger.error(
                f"Erro ao verificar RouteWatch {route.id}: {e}", 
                exc_info=True
            )
            return None
    
    def _validate_flight_dates(self, route: RouteWatch, offer: dict) -> Optional[str]:
        """Valida se as datas dos voos correspondem às datas solicitadas.
        
        Args:
            route: RouteWatch com as datas solicitadas
            offer: Oferta com as datas dos voos encontrados
            
        Returns:
            str: Mensagem de aviso se houver discrepância, None caso contrário
        """
        from datetime import datetime, date
        
        try:
            requested_departure = route.departure_date
            requested_return = route.return_date
            
            warnings = []
            
            # Verificar data de ida
            if offer.get("departure_at"):
                flight_departure_str = offer["departure_at"]
                # Extrair apenas a data (ignorar horário)
                if 'T' in flight_departure_str:
                    flight_departure_date = datetime.fromisoformat(flight_departure_str.replace('Z', '')).date()
                else:
                    flight_departure_date = datetime.strptime(flight_departure_str[:10], '%Y-%m-%d').date()
                
                if flight_departure_date != requested_departure:
                    warnings.append(f"Data de ida: solicitada {requested_departure}, encontrada {flight_departure_date}")
            
            # Verificar data de volta
            if offer.get("return_at"):
                flight_return_str = offer["return_at"]
                # Extrair apenas a data (ignorar horário)
                if 'T' in flight_return_str:
                    flight_return_date = datetime.fromisoformat(flight_return_str.replace('Z', '')).date()
                else:
                    flight_return_date = datetime.strptime(flight_return_str[:10], '%Y-%m-%d').date()
                
                if flight_return_date != requested_return:
                    warnings.append(f"Data de volta: solicitada {requested_return}, encontrada {flight_return_date}")
            
            if warnings:
                return "Datas dos voos não correspondem às solicitadas: " + "; ".join(warnings)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao validar datas: {e}")
            return None
    
    def _validate_exact_dates(self, route: RouteWatch, offer: dict) -> Optional[str]:
        """Valida se as datas dos voos correspondem exatamente às datas solicitadas (modo exato).
        
        Args:
            route: RouteWatch com as datas solicitadas
            offer: Oferta com as datas dos voos encontrados
            
        Returns:
            str: Mensagem de erro se houver discrepância, None caso contrário
        """
        from datetime import datetime
        
        try:
            requested_departure = route.departure_date
            requested_return = route.return_date
            
            errors = []
            
            # Verificar data de ida
            if offer.get("departure_at"):
                flight_departure_str = offer["departure_at"]
                # Extrair apenas a data (ignorar horário)
                if 'T' in flight_departure_str:
                    flight_departure_date = datetime.fromisoformat(flight_departure_str.replace('Z', '')).date()
                else:
                    flight_departure_date = datetime.strptime(flight_departure_str[:10], '%Y-%m-%d').date()
                
                if flight_departure_date != requested_departure:
                    errors.append(f"Data de ida: solicitada {requested_departure}, encontrada {flight_departure_date}")
            
            # Verificar data de volta
            if offer.get("return_at"):
                flight_return_str = offer["return_at"]
                # Extrair apenas a data (ignorar horário)
                if 'T' in flight_return_str:
                    flight_return_date = datetime.fromisoformat(flight_return_str.replace('Z', '')).date()
                else:
                    flight_return_date = datetime.strptime(flight_return_str[:10], '%Y-%m-%d').date()
                
                if flight_return_date != requested_return:
                    errors.append(f"Data de volta: solicitada {requested_return}, encontrada {flight_return_date}")
            
            if errors:
                return "Datas não correspondem (modo exato): " + "; ".join(errors)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao validar datas exatas: {e}")
            return None
