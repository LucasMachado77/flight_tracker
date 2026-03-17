"""Repositório para AlertLog"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.alert_log import AlertLog


class AlertLogRepository:
    """Repositório para operações CRUD de AlertLog"""
    
    def __init__(self, session: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            session: Sessão SQLAlchemy
        """
        self.session = session
    
    def create(self, alert_log: AlertLog) -> AlertLog:
        """
        Cria um novo AlertLog no banco de dados.
        
        Args:
            alert_log: Instância de AlertLog a ser criada
            
        Returns:
            AlertLog criado com ID atribuído
        """
        self.session.add(alert_log)
        self.session.commit()
        self.session.refresh(alert_log)
        return alert_log
    
    def find_by_id(self, alert_id: int) -> Optional[AlertLog]:
        """
        Busca um AlertLog por ID.
        
        Args:
            alert_id: ID do AlertLog
            
        Returns:
            AlertLog encontrado ou None se não existir
        """
        return self.session.query(AlertLog).filter(AlertLog.id == alert_id).first()
    
    def get_last_alert(self, route_id: int) -> Optional[AlertLog]:
        """
        Retorna o último alerta enviado para uma RouteWatch.
        
        Args:
            route_id: ID da RouteWatch
            
        Returns:
            AlertLog mais recente ou None se não houver alertas
        """
        return self.session.query(AlertLog).filter(
            AlertLog.route_watch_id == route_id
        ).order_by(AlertLog.sent_at.desc()).first()
    
    def find_by_route(self, route_id: int) -> List[AlertLog]:
        """
        Busca todos os AlertLog de uma RouteWatch específica.
        
        Args:
            route_id: ID da RouteWatch
            
        Returns:
            Lista de AlertLog da rota especificada, ordenados por data descendente
        """
        return self.session.query(AlertLog).filter(
            AlertLog.route_watch_id == route_id
        ).order_by(AlertLog.sent_at.desc()).all()
    
    def find_by_snapshot(self, snapshot_id: int) -> List[AlertLog]:
        """
        Busca todos os AlertLog de um PriceSnapshot específico.
        
        Args:
            snapshot_id: ID do PriceSnapshot
            
        Returns:
            Lista de AlertLog do snapshot especificado
        """
        return self.session.query(AlertLog).filter(
            AlertLog.price_snapshot_id == snapshot_id
        ).order_by(AlertLog.sent_at.desc()).all()
    
    def find_all(self) -> List[AlertLog]:
        """
        Busca todos os AlertLog cadastrados.
        
        Returns:
            Lista de todos os AlertLog
        """
        return self.session.query(AlertLog).order_by(AlertLog.sent_at.desc()).all()
    
    def delete(self, alert_log: AlertLog) -> None:
        """
        Remove um AlertLog do banco de dados.
        
        Args:
            alert_log: Instância de AlertLog a ser removida
        """
        self.session.delete(alert_log)
        self.session.commit()
