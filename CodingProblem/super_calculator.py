def calculate_super_balance(current_balance: float, yearly_deposit: float, avg_growth: float, years: int) -> float:
    """
    Calculate super balance after a given number of years.
    
    Args:
        current_balance: Starting balance in dollars
        yearly_deposit: Amount deposited each year in dollars
        avg_growth: Average annual growth rate (e.g., 0.07 for 7%)
        years: Number of years to project
    
    Returns:
        Final balance after the specified years
    """
    balance = current_balance
    
    for year in range(1, years + 1):
        # Add yearly deposit at start of year, then apply growth
        balance = (balance + yearly_deposit) * (1 + avg_growth)
    
    return balance


def print_yearly_breakdown(current_balance: float, yearly_deposit: float, avg_growth: float, years: int) -> None:
    """Print a year-by-year breakdown of super balance growth."""
    balance = current_balance
    
    print(f"{'Year':<6} {'Start Balance':>15} {'Deposit':>12} {'Growth':>12} {'End Balance':>15}")
    print("-" * 62)
    
    for year in range(1, years + 1):
        start_balance = balance
        balance += yearly_deposit
        growth = balance * avg_growth
        balance += growth
        
        print(f"{year:<6} ${start_balance:>14,.2f} ${yearly_deposit:>11,.2f} ${growth:>11,.2f} ${balance:>14,.2f}")
    
    print("-" * 62)
    print(f"Final Balance: ${balance:,.2f}")


if __name__ == "__main__":
    # Example usage
    current_balance = 130000    # $50,000 starting balance
    yearly_deposit = 18000     # $15,000 per year
    avg_growth = 0.07          # 7% average growth
    years = 32                 # 30 years until retirement
    
    final_balance = calculate_super_balance(current_balance, yearly_deposit, avg_growth, years)
    print(f"\nFinal super balance after {years} years: ${final_balance:,.2f}\n")
    
    print("Yearly Breakdown:")
    print_yearly_breakdown(current_balance, yearly_deposit, avg_growth, years)
