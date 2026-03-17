"""Database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


def get_normalized_database_url() -> str:
    """
    Normaliza a URL de banco de dados para o formato esperado pelo SQLAlchemy.

    - Se for PostgreSQL simples (`postgresql://`), converte para usar o driver psycopg3
      explícito (`postgresql+psycopg://`), que é compatível com o pacote `psycopg[binary]`.
    - Para outros bancos (ex.: SQLite), retorna a URL original sem alterações.
    """
    # Se a URL começar com o esquema padrão do PostgreSQL, forçamos o uso do driver psycopg3
    if settings.database_url.startswith("postgresql://"):
        return settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Para SQLite (ou qualquer outro esquema), usamos a URL como está
    return settings.database_url


# Cria o engine do SQLAlchemy usando a URL normalizada
engine = create_engine(
    get_normalized_database_url(),
    # Para SQLite, é necessário este connect_args específico; para outros bancos, deixamos vazio
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_session() -> Session:
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables():
    """
    Create all database tables.
    
    This function should be called during application initialization
    to ensure all tables exist in the database.
    """
    Base.metadata.create_all(bind=engine)
