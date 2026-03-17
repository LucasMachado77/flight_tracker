"""Repositório para PriceSnapshot"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.price_snapshot import PriceSnapshot


class PriceSnapshotRepository:
    """Repositório para operações CRUD de PriceSnapshot"""
    
    def __init__(self, session: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            session: Sessão SQLAlchemy
        """
        self.session = session
    
    def create(self, snapshot: PriceSnapshot) -> PriceSnapshot:
        """
        Cria um novo PriceSnapshot no banco de dados.
        
        Args:
            snapshot: Instância de PriceSnapshot a ser criada
            
        Returns:
            PriceSnapshot criado com ID atribuído
        """
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot
    
    def find_by_id(self, snapshot_id: int) -> Optional[PriceSnapshot]:
        """
        Busca um PriceSnapshot por ID.
        
        Args:
            snapshot_id: ID do PriceSnapshot
            
        Returns:
            PriceSnapshot encontrado ou None se não existir
        """
        return self.session.query(PriceSnapshot).filter(PriceSnapshot.id == snapshot_id).first()
    
    def find_by_route(
        self, 
        route_id: int, 
        order_by: str = "searched_at", 
        desc: bool = True
    ) -> List[PriceSnapshot]:
        """
        Busca todos os PriceSnapshot de uma RouteWatch específica.
        
        Args:
            route_id: ID da RouteWatch
            order_by: Campo para ordenação (padrão: "searched_at")
            desc: Se True, ordena em ordem descendente (padrão: True)
            
        Returns:
            Lista de PriceSnapshot da rota especificada
        """
        query = self.session.query(PriceSnapshot).filter(
            PriceSnapshot.route_watch_id == route_id
        )
        
        if desc:
            query = query.order_by(getattr(PriceSnapshot, order_by).desc())
        else:
            query = query.order_by(getattr(PriceSnapshot, order_by))
        
        return query.all()
    
    def get_min_price(self, route_id: int) -> Optional[float]:
        """
        Retorna o menor preço histórico de uma RouteWatch.
        
        Args:
            route_id: ID da RouteWatch
            
        Returns:
            Menor preço total registrado ou None se não houver snapshots
        """
        result = self.session.query(func.min(PriceSnapshot.price_total)).filter(
            PriceSnapshot.route_watch_id == route_id
        ).scalar()
        return result
    
    def find_all(self) -> List[PriceSnapshot]:
        """
        Busca todos os PriceSnapshot cadastrados.
        
        Returns:
            Lista de todos os PriceSnapshot
        """
        return self.session.query(PriceSnapshot).order_by(PriceSnapshot.searched_at.desc()).all()
    
    def delete(self, snapshot: PriceSnapshot) -> None:
        """
        Remove um PriceSnapshot do banco de dados.
        
        Args:
            snapshot: Instância de PriceSnapshot a ser removida
        """
        self.session.delete(snapshot)
        self.session.commit()
