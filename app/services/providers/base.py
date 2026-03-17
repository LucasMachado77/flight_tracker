"""Abstract interface for flight data providers.

This module defines the Protocol for flight data providers, allowing the system
to integrate with different flight search APIs while maintaining a consistent
internal interface.
"""

from typing import Protocol


class FlightProvider(Protocol):
    """Interface para provedores de dados de voos.
    
    Esta interface abstrata permite que o sistema se comunique com diferentes
    provedores de dados de voos (SerpApi, Skyscanner, etc.) através de uma
    interface padronizada, facilitando a troca de provedores no futuro.
    
    Valida: Requisito 7.1 - Comunicação através de interface abstrata
    """
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        adults: int = 1,
        cabin_class: str = "ECONOMY",
        currency: str = "EUR",
    ) -> dict:
        """Busca voos e retorna resposta bruta do provider.
        
        Args:
            origin: Código IATA do aeroporto de origem (ex: "LIS")
            destination: Código IATA do aeroporto de destino (ex: "GRU")
            departure_date: Data de ida no formato YYYY-MM-DD
            return_date: Data de volta no formato YYYY-MM-DD
            adults: Número de passageiros adultos (padrão: 1)
            cabin_class: Classe da cabine - ECONOMY, BUSINESS, FIRST (padrão: ECONOMY)
            currency: Código da moeda - EUR, USD, BRL, etc. (padrão: EUR)
        
        Returns:
            dict: Resposta bruta do provider em formato JSON/dict
            
        Raises:
            Exception: Erros de comunicação com o provider (timeout, autenticação, etc.)
        """
        ...
