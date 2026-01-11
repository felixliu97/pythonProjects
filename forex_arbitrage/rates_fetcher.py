"""
Forex exchange rate fetcher using frankfurter.app (free, no API key required)
"""
import requests
from typing import Dict

# Major forex currencies
MAJOR_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]

API_BASE_URL = "https://api.frankfurter.app/latest"


def fetch_exchange_rates(base_currency: str = "USD") -> Dict[str, float]:
    """
    Fetch exchange rates for a base currency against all major currencies.
    
    Args:
        base_currency: The base currency code (e.g., "USD")
    
    Returns:
        Dictionary of currency code to exchange rate
    """
    symbols = ",".join([c for c in MAJOR_CURRENCIES if c != base_currency])
    
    response = requests.get(
        API_BASE_URL,
        params={"from": base_currency, "to": symbols},
        timeout=10
    )
    response.raise_for_status()
    
    data = response.json()
    rates = data.get("rates", {})
    
    # Add the base currency with rate 1.0
    rates[base_currency] = 1.0
    
    return rates


def build_rate_matrix() -> Dict[str, Dict[str, float]]:
    """
    Build a complete exchange rate matrix for all major currency pairs.
    
    Returns:
        Nested dictionary: matrix[from_currency][to_currency] = rate
    """
    matrix = {}
    
    for base in MAJOR_CURRENCIES:
        print(f"  Fetching rates for {base}...")
        rates = fetch_exchange_rates(base)
        matrix[base] = rates
    
    return matrix


if __name__ == "__main__":
    # Quick test
    print("Testing rate fetcher...")
    rates = fetch_exchange_rates("USD")
    print(f"USD rates: {rates}")
