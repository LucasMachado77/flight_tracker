"""SerpApi Google Flights provider implementation.

This module implements the FlightProvider interface for SerpApi using the
Google Flights engine. It handles API communication, response normalization,
and offer processing.

Valida: Requisitos 7.2, 7.3, 7.4, 7.5
"""

import httpx
from typing import Optional


class SerpApiGoogleFlightsProvider:
    """Provider para SerpApi usando Google Flights engine.
    
    Esta implementação concreta do FlightProvider se comunica com a SerpApi
    usando o motor Google Flights para buscar preços de passagens aéreas.
    
    Attributes:
        api_key: Chave de API da SerpApi
        base_url: URL base da API SerpApi
        timeout: Timeout em segundos para requisições HTTP
    
    Valida: Requisito 7.1 - Implementação concreta de provider
    """
    
    def __init__(self, api_key: str, timeout: float = 30.0):
        """Inicializa o provider SerpApi.
        
        Args:
            api_key: Chave de API da SerpApi
            timeout: Timeout em segundos para requisições (padrão: 30.0)
        """
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search.json"
        self.timeout = timeout
    
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
        """Consulta voos via SerpApi Google Flights.
        
        Realiza uma requisição HTTP GET para a SerpApi com os parâmetros
        de busca especificados e retorna a resposta JSON bruta.
        
        Args:
            origin: Código IATA do aeroporto de origem (ex: "LIS")
            destination: Código IATA do aeroporto de destino (ex: "GRU")
            departure_date: Data de ida no formato YYYY-MM-DD
            return_date: Data de volta no formato YYYY-MM-DD
            adults: Número de passageiros adultos
            cabin_class: Classe da cabine (ECONOMY, BUSINESS, FIRST)
            currency: Código da moeda (EUR, USD, BRL)
        
        Returns:
            dict: Resposta JSON bruta da SerpApi
            
        Raises:
            httpx.HTTPError: Erro na comunicação com a API
            httpx.TimeoutException: Timeout na requisição
        
        Valida: Requisito 7.2 - Normalização de resposta do provider
        """
        # Mapear classes de cabine para formato SerpApi
        cabin_mapping = {
            "ECONOMY": "1",
            "PREMIUM_ECONOMY": "2", 
            "BUSINESS": "3",
            "FIRST": "4"
        }
        
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "return_date": return_date,
            "currency": currency,
            "adults": str(adults),
            "travel_class": cabin_mapping.get(cabin_class, "1"),
            "type": "1",  # Round trip (1 = round trip, 2 = one way)
            "hl": "pt-PT",
            "api_key": self.api_key,
        }
        
        # Log da consulta para debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"SerpApi consulta: {origin}->{destination}, ida:{departure_date}, volta:{return_date}")
        
        response = httpx.get(self.base_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        
        # Log da resposta para debug
        if "best_flights" in result:
            logger.info(f"SerpApi retornou {len(result['best_flights'])} melhores voos")
        if "other_flights" in result:
            logger.info(f"SerpApi retornou {len(result['other_flights'])} outros voos")
        if "error" in result:
            logger.error(f"SerpApi erro: {result['error']}")
            
        return result
    
    def normalize_response(self, raw_response: dict) -> dict:
        """Normaliza resposta da SerpApi para formato interno.
        
        Extrai ofertas de voos da resposta bruta da SerpApi e as converte
        para um formato padronizado interno. A SerpApi retorna ofertas em
        "best_flights" e "other_flights".
        
        Args:
            raw_response: Resposta bruta da SerpApi
            
        Returns:
            dict: Resposta normalizada com estrutura:
                {
                    "provider": "serpapi_google_flights",
                    "offers": [lista de ofertas normalizadas],
                    "raw_response": resposta bruta original
                }
        
        Valida: Requisito 7.2 - Normalização de resposta do provider
        """
        offers = []
        
        # SerpApi retorna ofertas em "best_flights" ou "other_flights"
        all_flights = []
        if "best_flights" in raw_response:
            all_flights.extend(raw_response["best_flights"])
        if "other_flights" in raw_response:
            all_flights.extend(raw_response["other_flights"])
        
        for flight in all_flights:
            offer = self._normalize_offer(flight)
            if offer:
                offers.append(offer)
        
        return {
            "provider": "serpapi_google_flights",
            "offers": offers,
            "raw_response": raw_response
        }
    
    def _normalize_offer(self, raw_offer: dict) -> Optional[dict]:
        """Normaliza uma oferta individual.
        
        Extrai campos relevantes de uma oferta bruta da SerpApi e os
        converte para o formato interno padronizado. Ofertas inválidas
        ou incompletas retornam None.
        
        Args:
            raw_offer: Oferta bruta da SerpApi
            
        Returns:
            dict: Oferta normalizada com campos:
                - price_total: Preço total da oferta
                - currency: Código da moeda
                - airline: Nome da companhia aérea
                - airline_code: Código da companhia aérea
                - departure_at: Horário de partida (ISO format)
                - return_at: Horário de retorno (ISO format)
                - stops: Número de escalas
                - offer_hash: Hash/token da oferta
            None: Se a oferta for inválida ou incompleta
        
        Valida: Requisito 7.3 - Extração de campos da resposta
        """
        try:
            flights = raw_offer.get("flights", [])
            if not flights:
                return None
            
            # Primeiro voo é ida
            outbound = flights[0]
            
            # Extrair informações de horários mais detalhadas
            departure_time = None
            return_time = None
            
            # Comentário (pt-BR): para a ida usamos o primeiro trecho
            if outbound and "departure_airport" in outbound:
                departure_time = outbound["departure_airport"].get("time")
                # Tentar também "departure_time" se "time" não existir
                if not departure_time:
                    departure_time = outbound.get("departure_time")
            
            # Comentário (pt-BR): para a volta, percorremos todos os trechos e pegamos
            # o último horário de chegada conhecido (melhor aproximação da chegada final).
            for segment in flights:
                candidate = None
                if "arrival_airport" in segment:
                    candidate = segment["arrival_airport"].get("time")
                if not candidate:
                    candidate = segment.get("arrival_time")
                
                if candidate:
                    return_time = candidate
            
            # Converter para formato ISO se necessário
            if departure_time and not departure_time.endswith('Z') and 'T' not in departure_time:
                # Se for apenas data, adicionar horário padrão
                if len(departure_time) == 10:  # YYYY-MM-DD
                    departure_time = departure_time + "T12:00:00"
            
            if return_time and isinstance(return_time, str) and not return_time.endswith('Z') and 'T' not in return_time:
                # Se for apenas data, adicionar horário padrão
                if len(return_time) == 10:  # YYYY-MM-DD
                    return_time = return_time + "T12:00:00"
            
            return {
                "price_total": raw_offer.get("price"),
                "currency": raw_offer.get("currency", "EUR"),
                "airline": outbound.get("airline"),
                "airline_code": outbound.get("airline_code"),
                "departure_at": departure_time,
                "return_at": return_time,
                "stops": len(flights) - 1,
                "offer_hash": raw_offer.get("booking_token", ""),
            }
        except (KeyError, TypeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erro ao normalizar oferta: {e}, dados: {raw_offer}")
            return None
