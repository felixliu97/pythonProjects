"""
Triangular Forex Arbitrage Detector

Detects profit opportunities by exchanging through 3 currencies.
Example: USD → AUD → EUR → USD
"""
from itertools import permutations
from typing import List, Tuple, Dict
from rates_fetcher import build_rate_matrix, MAJOR_CURRENCIES


def calculate_triangular_return(
    matrix: Dict[str, Dict[str, float]],
    currency_a: str,
    currency_b: str,
    currency_c: str
) -> float:
    """
    Calculate the return of a triangular exchange: A → B → C → A
    
    Returns:
        The product of exchange rates. If > 1.0, arbitrage exists.
    """
    rate_ab = matrix[currency_a].get(currency_b, 0)
    rate_bc = matrix[currency_b].get(currency_c, 0)
    rate_ca = matrix[currency_c].get(currency_a, 0)
    
    if rate_ab == 0 or rate_bc == 0 or rate_ca == 0:
        return 0.0
    
    return rate_ab * rate_bc * rate_ca


def find_arbitrage_opportunities(
    matrix: Dict[str, Dict[str, float]],
    min_profit_threshold: float = 0.05
) -> List[Tuple[str, str, str, float]]:
    """
    Find all triangular arbitrage opportunities.
    
    Args:
        matrix: Exchange rate matrix
        min_profit_threshold: Minimum profit % to consider (e.g., 0.1 for 0.1%)
    
    Returns:
        List of (currency_a, currency_b, currency_c, profit_percent)
    """
    opportunities = []
    
    # Check all permutations of 3 currencies
    for trio in permutations(MAJOR_CURRENCIES, 3):
        currency_a, currency_b, currency_c = trio
        
        result = calculate_triangular_return(matrix, currency_a, currency_b, currency_c)
        profit_percent = (result - 1.0) * 100
        
        if profit_percent > min_profit_threshold:
            opportunities.append((currency_a, currency_b, currency_c, profit_percent))
    
    # Sort by profit descending
    opportunities.sort(key=lambda x: x[3], reverse=True)
    
    return opportunities


def display_results(opportunities: List[Tuple[str, str, str, float]], total_checked: int):
    """Display arbitrage scan results."""
    print()
    
    if opportunities:
        print("🔥 ARBITRAGE OPPORTUNITIES FOUND:")
        print("-" * 45)
        for a, b, c, profit in opportunities:
            print(f"  ✓ {a} → {b} → {c} → {a} : +{profit:.3f}%")
        print("-" * 45)
        print(f"  {len(opportunities)} opportunities found out of {total_checked} trios")
    else:
        print("No arbitrage opportunities detected.")
        print(f"Checked {total_checked} currency trios.")
    
    print()


def main():
    """Main entry point."""
    print("=" * 50)
    print("  TRIANGULAR FOREX ARBITRAGE DETECTOR")
    print("=" * 50)
    print()
    print(f"Scanning {len(MAJOR_CURRENCIES)} major currencies: {', '.join(MAJOR_CURRENCIES)}")
    print()
    
    print("Fetching live exchange rates...")
    try:
        matrix = build_rate_matrix()
    except Exception as e:
        print(f"❌ Error fetching rates: {e}")
        return
    
    print()
    print("Analyzing triangular arbitrage opportunities...")
    
    # Calculate total permutations: P(8,3) = 8 * 7 * 6 = 336
    total_trios = len(MAJOR_CURRENCIES) * (len(MAJOR_CURRENCIES) - 1) * (len(MAJOR_CURRENCIES) - 2)
    
    opportunities = find_arbitrage_opportunities(matrix)
    display_results(opportunities, total_trios)


if __name__ == "__main__":
    main()
