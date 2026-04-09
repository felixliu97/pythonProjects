import argparse

def calculate_owner_earnings(net_income, da, capex):
    """
    Buffett's Owner Earnings: Net Income + Depreciation/Amortization - Required CapEx
    """
    return net_income + da - capex

def calculate_roic(operating_income, tax_rate, total_assets, current_liabilities):
    """
    Return on Invested Capital: NOPAT / (Total Assets - Current Liabilities)
    """
    nopat = operating_income * (1 - tax_rate)
    invested_capital = total_assets - current_liabilities
    if invested_capital == 0:
        return 0
    return (nopat / invested_capital) * 100

def main():
    parser = argparse.ArgumentParser(description="Buffett Style Financial Metrics Calculator")
    parser.add_argument("--income", type=float, help="Net Income", required=True)
    parser.add_argument("--da", type=float, help="Depreciation & Amortization", required=True)
    parser.add_argument("--capex", type=float, help="Capital Expenditure (Maintenance)", required=True)
    parser.add_argument("--op_income", type=float, help="Operating Income (EBIT)")
    parser.add_argument("--tax", type=float, default=0.25, help="Tax Rate (default 0.25)")
    parser.add_argument("--assets", type=float, help="Total Assets")
    parser.add_argument("--liabilities", type=float, help="Current Liabilities")

    args = parser.parse_args()

    oe = calculate_owner_earnings(args.income, args.da, args.capex)
    print(f"\n--- Buffett Metrics ---")
    print(f"Owner Earnings: {oe:,.2f}")
    
    if args.op_income and args.assets and args.liabilities:
        roic = calculate_roic(args.op_income, args.tax, args.assets, args.liabilities)
        print(f"ROIC: {roic:.2f}%")
        if roic > 15:
            print("Status: HIGH ROIC (Wonderful Business candidate)")
        else:
            print("Status: SUB-PAR ROIC (Check for moat issues)")

if __name__ == "__main__":
    main()
