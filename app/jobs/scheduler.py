"""Scheduler para execução periódica de verificação de preços"""
import logging
import sys
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from app.core.config import settings
from app.core.database import SessionLocal, create_tables
from app.repositories.route_watch_repository import RouteWatchRepository
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.repositories.alert_log_repository import AlertLogRepository
from app.services.providers.serpapi_google_flights import SerpApiGoogleFlightsProvider
from app.services.history_service import HistoryService
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.services.flight_search_service import FlightSearchService


def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def run_price_check():
    """Executar verificação de preços"""
    logger = logging.getLogger(__name__)
    logger.info("Iniciando job de verificação de preços")
    
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
        
        # Buscar rotas ativas
        active_routes = route_repo.find_all_active()
        logger.info(f"Processando {len(active_routes)} rotas ativas")
        
        # Processar cada rota
        for route in active_routes:
            try:
                flight_service.check_route_price(route)
            except Exception as e:
                logger.error(f"Erro ao processar RouteWatch {route.id}: {e}", exc_info=True)
        
        logger.info("Job de verificação concluído")
        
    except Exception as e:
        logger.error(f"Erro crítico no job: {e}", exc_info=True)
    finally:
        session.close()


def main():
    """Função principal"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando scheduler de verificação de preços")
    
    # Garantir que tabelas existem
    create_tables()
    
    # Criar scheduler
    scheduler = BlockingScheduler()
    
    # Agendar job a cada 6 horas
    scheduler.add_job(
        run_price_check,
        trigger=IntervalTrigger(hours=6),
        id='price_check_job',
        name='Verificação de Preços',
        replace_existing=True
    )
    
    # Executar uma vez imediatamente
    logger.info("Executando verificação inicial...")
    run_price_check()
    
    try:
        logger.info("Scheduler iniciado. Pressione Ctrl+C para parar.")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler interrompido pelo usuário")
        scheduler.shutdown()


if __name__ == "__main__":
    main()