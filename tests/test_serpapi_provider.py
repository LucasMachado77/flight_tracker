"""Unit tests for SerpApiGoogleFlightsProvider.

Tests basic functionality of the SerpApi provider including response
normalization and offer processing.
"""

import pytest
from app.services.providers.serpapi_google_flights import SerpApiGoogleFlightsProvider


class TestSerpApiGoogleFlightsProvider:
    """Test suite for SerpApiGoogleFlightsProvider."""
    
    def test_provider_initialization(self):
        """Test that provider initializes with correct attributes."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key", timeout=15.0)
        
        assert provider.api_key == "test_key"
        assert provider.timeout == 15.0
        assert provider.base_url == "https://serpapi.com/search.json"
    
    def test_provider_default_timeout(self):
        """Test that provider uses default timeout when not specified."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        assert provider.timeout == 30.0
    
    def test_normalize_response_with_best_flights(self):
        """Test normalization of response containing best_flights."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_response = {
            "best_flights": [
                {
                    "price": 450.50,
                    "currency": "EUR",
                    "booking_token": "token123",
                    "flights": [
                        {
                            "airline": "TAP Air Portugal",
                            "airline_code": "TP",
                            "departure_airport": {"time": "2024-07-15 10:30"},
                            "arrival_airport": {"time": "2024-07-15 18:45"}
                        },
                        {
                            "airline": "TAP Air Portugal",
                            "airline_code": "TP",
                            "departure_airport": {"time": "2024-07-20 14:00"},
                            "arrival_airport": {"time": "2024-07-20 22:15"}
                        }
                    ]
                }
            ]
        }
        
        result = provider.normalize_response(raw_response)
        
        assert result["provider"] == "serpapi_google_flights"
        assert len(result["offers"]) == 1
        assert result["raw_response"] == raw_response
        
        offer = result["offers"][0]
        assert offer["price_total"] == 450.50
        assert offer["currency"] == "EUR"
        assert offer["airline"] == "TAP Air Portugal"
        assert offer["airline_code"] == "TP"
        assert offer["departure_at"] == "2024-07-15 10:30"
        assert offer["return_at"] == "2024-07-20 22:15"
        assert offer["stops"] == 1
        assert offer["offer_hash"] == "token123"
    
    def test_normalize_response_with_other_flights(self):
        """Test normalization of response containing other_flights."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_response = {
            "other_flights": [
                {
                    "price": 550.00,
                    "currency": "EUR",
                    "booking_token": "token456",
                    "flights": [
                        {
                            "airline": "Lufthansa",
                            "airline_code": "LH",
                            "departure_airport": {"time": "2024-07-15 08:00"},
                            "arrival_airport": {"time": "2024-07-15 16:30"}
                        },
                        {
                            "airline": "Lufthansa",
                            "airline_code": "LH",
                            "departure_airport": {"time": "2024-07-20 12:00"},
                            "arrival_airport": {"time": "2024-07-20 20:30"}
                        }
                    ]
                }
            ]
        }
        
        result = provider.normalize_response(raw_response)
        
        assert len(result["offers"]) == 1
        assert result["offers"][0]["airline"] == "Lufthansa"
    
    def test_normalize_response_with_both_flight_types(self):
        """Test normalization when both best_flights and other_flights are present."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_response = {
            "best_flights": [
                {
                    "price": 400.00,
                    "currency": "EUR",
                    "booking_token": "best_token",
                    "flights": [
                        {
                            "airline": "TAP",
                            "airline_code": "TP",
                            "departure_airport": {"time": "2024-07-15 10:00"},
                            "arrival_airport": {"time": "2024-07-15 18:00"}
                        },
                        {
                            "airline": "TAP",
                            "airline_code": "TP",
                            "departure_airport": {"time": "2024-07-20 10:00"},
                            "arrival_airport": {"time": "2024-07-20 18:00"}
                        }
                    ]
                }
            ],
            "other_flights": [
                {
                    "price": 500.00,
                    "currency": "EUR",
                    "booking_token": "other_token",
                    "flights": [
                        {
                            "airline": "Lufthansa",
                            "airline_code": "LH",
                            "departure_airport": {"time": "2024-07-15 12:00"},
                            "arrival_airport": {"time": "2024-07-15 20:00"}
                        },
                        {
                            "airline": "Lufthansa",
                            "airline_code": "LH",
                            "departure_airport": {"time": "2024-07-20 12:00"},
                            "arrival_airport": {"time": "2024-07-20 20:00"}
                        }
                    ]
                }
            ]
        }
        
        result = provider.normalize_response(raw_response)
        
        assert len(result["offers"]) == 2
        assert result["offers"][0]["price_total"] == 400.00
        assert result["offers"][1]["price_total"] == 500.00
    
    def test_normalize_response_empty(self):
        """Test normalization of empty response."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_response = {}
        result = provider.normalize_response(raw_response)
        
        assert result["provider"] == "serpapi_google_flights"
        assert result["offers"] == []
        assert result["raw_response"] == raw_response
    
    def test_normalize_offer_with_direct_flight(self):
        """Test normalization of direct flight (no stops)."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_offer = {
            "price": 300.00,
            "currency": "EUR",
            "booking_token": "direct_token",
            "flights": [
                {
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_airport": {"time": "2024-07-15 10:00"},
                    "arrival_airport": {"time": "2024-07-15 18:00"}
                }
            ]
        }
        
        offer = provider._normalize_offer(raw_offer)
        
        assert offer is not None
        assert offer["stops"] == 0
        assert offer["return_at"] is None
    
    def test_normalize_offer_with_multiple_stops(self):
        """Test normalization of flight with multiple stops."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_offer = {
            "price": 600.00,
            "currency": "EUR",
            "booking_token": "multi_stop_token",
            "flights": [
                {
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_airport": {"time": "2024-07-15 10:00"},
                    "arrival_airport": {"time": "2024-07-15 14:00"}
                },
                {
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_airport": {"time": "2024-07-15 16:00"},
                    "arrival_airport": {"time": "2024-07-15 20:00"}
                },
                {
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_airport": {"time": "2024-07-20 10:00"},
                    "arrival_airport": {"time": "2024-07-20 18:00"}
                }
            ]
        }
        
        offer = provider._normalize_offer(raw_offer)
        
        assert offer is not None
        assert offer["stops"] == 2
    
    def test_normalize_offer_invalid_no_flights(self):
        """Test that offers without flights return None."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_offer = {
            "price": 300.00,
            "currency": "EUR",
            "flights": []
        }
        
        offer = provider._normalize_offer(raw_offer)
        
        assert offer is None
    
    def test_normalize_offer_invalid_missing_fields(self):
        """Test that offers with missing required fields return None."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_offer = {
            "price": 300.00,
            # Missing flights key
        }
        
        offer = provider._normalize_offer(raw_offer)
        
        assert offer is None
    
    def test_normalize_offer_default_currency(self):
        """Test that missing currency defaults to EUR."""
        provider = SerpApiGoogleFlightsProvider(api_key="test_key")
        
        raw_offer = {
            "price": 300.00,
            # No currency specified
            "booking_token": "token",
            "flights": [
                {
                    "airline": "TAP",
                    "airline_code": "TP",
                    "departure_airport": {"time": "2024-07-15 10:00"},
                    "arrival_airport": {"time": "2024-07-15 18:00"}
                }
            ]
        }
        
        offer = provider._normalize_offer(raw_offer)
        
        assert offer is not None
        assert offer["currency"] == "EUR"
