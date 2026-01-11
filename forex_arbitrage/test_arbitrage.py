"""
Unit tests for arbitrage detection logic
"""
import unittest
from arbitrage_detector import calculate_triangular_return, find_arbitrage_opportunities


class TestArbitrageDetection(unittest.TestCase):
    
    def test_no_arbitrage(self):
        """Test case where no arbitrage exists (product = 1.0)"""
        # Perfect market: rates are inverses
        matrix = {
            "USD": {"USD": 1.0, "EUR": 0.9, "GBP": 0.8},
            "EUR": {"USD": 1.1111, "EUR": 1.0, "GBP": 0.8889},
            "GBP": {"USD": 1.25, "EUR": 1.125, "GBP": 1.0},
        }
        
        result = calculate_triangular_return(matrix, "USD", "EUR", "GBP")
        # 0.9 * 0.8889 * 1.25 ≈ 1.0
        self.assertAlmostEqual(result, 1.0, places=2)
    
    def test_arbitrage_exists(self):
        """Test case where arbitrage opportunity exists"""
        # Imperfect market with profit opportunity
        matrix = {
            "USD": {"USD": 1.0, "EUR": 0.92, "GBP": 0.79},
            "EUR": {"USD": 1.09, "EUR": 1.0, "GBP": 0.86},
            "GBP": {"USD": 1.27, "EUR": 1.17, "GBP": 1.0},
        }
        
        result = calculate_triangular_return(matrix, "USD", "EUR", "GBP")
        # 0.92 * 0.86 * 1.27 = 1.0046
        self.assertGreater(result, 1.0)
        
        profit_percent = (result - 1.0) * 100
        print(f"\n  Test arbitrage: USD → EUR → GBP → USD = {profit_percent:.3f}% profit")
    
    def test_find_opportunities(self):
        """Test finding all opportunities in a rate matrix"""
        matrix = {
            "USD": {"USD": 1.0, "EUR": 0.92, "GBP": 0.79},
            "EUR": {"USD": 1.09, "EUR": 1.0, "GBP": 0.86},
            "GBP": {"USD": 1.27, "EUR": 1.17, "GBP": 1.0},
        }
        
        # Temporarily override MAJOR_CURRENCIES for test
        import arbitrage_detector
        original = arbitrage_detector.MAJOR_CURRENCIES
        arbitrage_detector.MAJOR_CURRENCIES = ["USD", "EUR", "GBP"]
        
        try:
            opportunities = find_arbitrage_opportunities(matrix)
            print(f"\n  Found {len(opportunities)} opportunities")
            for a, b, c, profit in opportunities:
                print(f"    {a} → {b} → {c} → {a}: {profit:.3f}%")
        finally:
            arbitrage_detector.MAJOR_CURRENCIES = original


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  ARBITRAGE DETECTION UNIT TESTS")
    print("=" * 50)
    unittest.main(verbosity=2)
