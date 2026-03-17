"""Scheduler em background que roda junto com a API"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import SessionLocal
from app.repositories.route_watch_repository import RouteWatchRepository
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.repositories.alert_log_repository import AlertLogRepository
from app.services.providers.serpapi_google_flights import SerpApiGoogleFlightsProvider
from app.services.history_service import HistoryService
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.services.flight_search_service import FlightSearchService
from app.core.config import settings


class BackgroundScheduler:
    """Scheduler que executa verificações de preço em background"""
    
    def __init__(self, check_interval_minutes: int = 360):  # 6 horas por padrão
        self.check_interval_minutes = check_interval_minutes
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Iniciar o scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        self.logger.info(f"Background scheduler iniciado (intervalo: {self.check_interval_minutes} minutos)")
    
    async def stop(self):
        """Parar o scheduler"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info("Background scheduler parado")
    
    async def _run_scheduler(self):
        """Loop principal do scheduler"""
        # Executar uma verificação inicial após 1 minuto
        await asyncio.sleep(60)
        
        while self.is_running:
            try:
                await self._run_price_check()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no scheduler: {e}", exc_info=True)
                # Aguardar 5 minutos antes de tentar novamente em caso de erro
                await asyncio.sleep(300)
    
    async def _run_price_check(self):
        """Executar verificação de preços"""
        self.logger.info("Iniciando verificação automática de preços")
        
        session = SessionLocal()
        
        try:
            # Criar repositórios
            route_repo = RouteWatchRepository(session)
            snapshot_repo = PriceSnapshotRepository(session)
            alert_repo = AlertLogRepository(session)
            
            # Criar provider
            provider = SerpApiGoogleFlightsProvider(
                api_key=settings.serpapi_api_key,
                timeout=settings.serpapi_timeout
            )
            
            # Criar serviços
            history_service = HistoryService(snapshot_repo, alert_repo)
            alert_service = AlertService(alert_repo)
            notification_service = NotificationService(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id
            )
            
            flight_service = FlightSearchService(
                provider=provider,
                history_service=history_service,
                alert_service=alert_service,
                notification_service=notification_service
            )
            
            # Buscar rotas ativas que precisam ser verificadas
            active_routes = route_repo.find_all_active()
            routes_to_check = []
            
            now = datetime.utcnow()
            
            for route in active_routes:
                # Verificar se é hora de checar esta rota baseado no intervalo individual
                last_snapshot = snapshot_repo.find_by_route(route.id, order_by="searched_at", desc=True)
                
                if not last_snapshot:
                    # Primeira verificação
                    routes_to_check.append(route)
                else:
                    # Verificar se passou o intervalo configurado
                    last_check = last_snapshot[0].searched_at
                    next_check = last_check + timedelta(minutes=route.check_interval_minutes)
                    
                    if now >= next_check:
                        routes_to_check.append(route)
            
            self.logger.info(f"Verificando {len(routes_to_check)} rotas de {len(active_routes)} ativas")
            
            # Processar cada rota
            success_count = 0
            error_count = 0
            
            for route in routes_to_check:
                try:
                    # Executar em thread separada para não bloquear
                    await asyncio.get_event_loop().run_in_executor(
                        None, flight_service.check_route_price, route
                    )
                    success_count += 1
                    
                    # Pequena pausa entre verificações para não sobrecarregar a API
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Erro ao processar RouteWatch {route.id}: {e}", exc_info=True)
            
            self.logger.info(f"Verificação concluída: {success_count} sucessos, {error_count} erros")
            
        except Exception as e:
            self.logger.error(f"Erro crítico na verificação automática: {e}", exc_info=True)
        finally:
            session.close()
    
    async def force_check_all(self):
        """Forçar verificação de todas as rotas ativas (para uso via API)"""
        if not self.is_running:
            return {"error": "Scheduler não está rodando"}
        
        try:
            await self._run_price_check()
            return {"success": True, "message": "Verificação forçada executada"}
        except Exception as e:
            self.logger.error(f"Erro na verificação forçada: {e}", exc_info=True)
            return {"error": str(e)}