"""Script para inicializar o banco de dados"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.database import create_tables, SessionLocal
from app.repositories.route_watch_repository import RouteWatchRepository
from app.models.route_watch import RouteWatch


def create_sample_data():
    """Criar dados de exemplo"""
    session = SessionLocal()
    repo = RouteWatchRepository(session)
    
    try:
        # Verificar se já existem dados
        existing_routes = repo.find_all()
        if existing_routes:
            print(f"Banco já contém {len(existing_routes)} rotas. Pulando criação de dados de exemplo.")
            return
        
        # Criar rotas de exemplo
        sample_routes = [
            RouteWatch(
                origin="LIS",
                destination="GRU",
                departure_date=date.today() + timedelta(days=60),
                return_date=date.today() + timedelta(days=75),
                adults=1,
                cabin_class="ECONOMY",
                currency="EUR",
                check_interval_minutes=360,
                notify_on_new_low=True,
            ),
            RouteWatch(
                origin="OPO",
                destination="NYC",
                departure_date=date.today() + timedelta(days=90),
                return_date=date.today() + timedelta(days=105),
                adults=2,
                cabin_class="BUSINESS",
                currency="EUR",
                check_interval_minutes=720,
                notify_on_new_low=True,
                min_price_difference=50.0,
                alert_cooldown_hours=24,
            ),
            RouteWatch(
                origin="LIS",
                destination="LON",
                departure_date=date.today() + timedelta(days=30),
                return_date=date.today() + timedelta(days=35),
                adults=1,
                cabin_class="ECONOMY",
                currency="EUR",
                check_interval_minutes=180,
                notify_on_new_low=True,
                is_active=False,  # Rota inativa para teste
            ),
        ]
        
        for route in sample_routes:
            repo.create(route)
        
        print(f"Criadas {len(sample_routes)} rotas de exemplo")
        
    finally:
        session.close()


def main():
    """Função principal"""
    print("Inicializando banco de dados...")
    
    # Criar tabelas
    create_tables()
    print("Tabelas criadas/verificadas com sucesso")
    
    # Perguntar se deve criar dados de exemplo
    create_samples = input("Criar dados de exemplo? (y/N): ").lower().strip()
    if create_samples in ['y', 'yes', 's', 'sim']:
        create_sample_data()
    
    print("Inicialização concluída!")


if __name__ == "__main__":
    main()