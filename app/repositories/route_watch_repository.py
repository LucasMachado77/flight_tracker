"""Repositório para RouteWatch"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.route_watch import RouteWatch


class RouteWatchRepository:
    """Repositório para operações CRUD de RouteWatch"""
    
    def __init__(self, session: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            session: Sessão SQLAlchemy
        """
        self.session = session
    
    def create(self, route: RouteWatch) -> RouteWatch:
        """
        Cria uma nova RouteWatch no banco de dados.
        
        Args:
            route: Instância de RouteWatch a ser criada
            
        Returns:
            RouteWatch criada com ID atribuído
        """
        self.session.add(route)
        self.session.commit()
        self.session.refresh(route)
        return route
    
    def find_by_id(self, route_id: int) -> Optional[RouteWatch]:
        """
        Busca uma RouteWatch por ID.
        
        Args:
            route_id: ID da RouteWatch
            
        Returns:
            RouteWatch encontrada ou None se não existir
        """
        return self.session.query(RouteWatch).filter(RouteWatch.id == route_id).first()
    
    def find_all(self) -> List[RouteWatch]:
        """
        Busca todas as RouteWatch cadastradas.
        
        Returns:
            Lista de todas as RouteWatch
        """
        return self.session.query(RouteWatch).order_by(RouteWatch.created_at.desc()).all()
    
    def find_all_active(self) -> List[RouteWatch]:
        """
        Busca todas as RouteWatch ativas.
        
        Returns:
            Lista de RouteWatch com is_active == True
        """
        return self.session.query(RouteWatch).filter(RouteWatch.is_active == True).all()
    
    def find_by_status(self, is_active: bool) -> List[RouteWatch]:
        """
        Busca RouteWatch por status.
        
        Args:
            is_active: Status desejado (True para ativas, False para inativas)
            
        Returns:
            Lista de RouteWatch com o status especificado
        """
        return self.session.query(RouteWatch).filter(
            RouteWatch.is_active == is_active
        ).order_by(RouteWatch.created_at.desc()).all()
    
    def update(self, route: RouteWatch) -> RouteWatch:
        """
        Atualiza uma RouteWatch existente.
        
        Args:
            route: Instância de RouteWatch com alterações
            
        Returns:
            RouteWatch atualizada
        """
        self.session.commit()
        self.session.refresh(route)
        return route
    
    def delete(self, route: RouteWatch) -> None:
        """
        Remove uma RouteWatch do banco de dados.
        
        Args:
            route: Instância de RouteWatch a ser removida
        """
        self.session.delete(route)
        self.session.commit()
