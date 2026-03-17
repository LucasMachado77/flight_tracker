"""Script para executar verificação periódica de preços"""
import logging
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
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


def main():
    """Função principal"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando verificação periódica de preços")
    
    # Garantir que tabelas existem
    create_tables()
    
    # Criar sessão do banco
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
        
        # Buscar todas as rotas ativas
        active_routes = route_repo.find_all_active()
        logger.info(f"Encontradas {len(active_routes)} rotas ativas para verificação")
        
        if not active_routes:
            logger.info("Nenhuma rota ativa encontrada")
            return
        
        # Processar cada rota
        success_count = 0
        error_count = 0
        
        for route in active_routes:
            logger.info(f"Processando RouteWatch {route.id}: {route.origin} → {route.destination}")
            
            try:
                snapshot = flight_service.check_route_price(route)
                if snapshot:
                    success_count += 1
                    logger.info(f"RouteWatch {route.id} processada com sucesso")
                else:
                    error_count += 1
                    logger.warning(f"RouteWatch {route.id} falhou na verificação")
            except Exception as e:
                error_count += 1
                logger.error(f"Erro ao processar RouteWatch {route.id}: {e}", exc_info=True)
        
        logger.info(f"Verificação concluída: {success_count} sucessos, {error_count} erros")
        
    except Exception as e:
        logger.error(f"Erro crítico na verificação: {e}", exc_info=True)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()