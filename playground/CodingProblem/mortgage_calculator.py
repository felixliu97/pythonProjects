import argparse

class Mortgage:
    def __init__(self, principal: float, interest_rate: float, term: int, extra_pay: float=0):
        self.principal = principal
        self.interest_rate = interest_rate
        self.term = term
        self.extra_pay = extra_pay

    def calculate_mortgage_repayment(self) -> float:
        monthly_interest_rate = self.interest_rate / 100 / 12
        term_in_months = self.term * 12
        # Handle zero interest rate edge case if needed, but standard formula assumption:
        if monthly_interest_rate == 0:
            return self.principal / term_in_months
        
        repayment = self.principal * (monthly_interest_rate / (1 - (1 + monthly_interest_rate) ** (-term_in_months)))
        return repayment

    def show_balance_projection(self):
        balance = self.principal
        print(f"Principal: {self.principal}, Interest rate: {self.interest_rate}")
        monthly_interest_rate = self.interest_rate / 100 / 12
        repayment = self.calculate_mortgage_repayment()
        print(f"Monthly repayment: {repayment:.2f}, Extra pay: {self.extra_pay:.2f}, Total repayment: {repayment + self.extra_pay:.2f}")
        payments_made = 0

        while balance > 0:
            interest_portion = balance * monthly_interest_rate
            principal_portion = repayment + self.extra_pay - interest_portion
            
            # Reduce balance
            balance -= principal_portion
            
            # Recalculate balance accurately (the original logic was slightly mixing terms, simpler to just subtract net principal paid)
            # Original: balance = balance - repayment - self.extra_pay + (balance * monthly_interest_rate)
            # If we reuse original logic structure for minimal logical drift:
            # balance = balance - (repayment + self.extra_pay) + (balance * monthly_interest_rate)
            # This is equivalent to new balance = old balance + interest - payment
            
            payments_made += 1
            if balance < 1:
                balance = 0
            # print(f"Month {payments_made} - Remaining balance: {balance}")

        total_paid = (repayment + self.extra_pay) * payments_made
        total_interest_paid = total_paid - self.principal
        print(f"Total terms: {payments_made} months ({payments_made/12:.1f} years)")
        print(f"Total paid: {total_paid:.2f}, Total interest paid: {total_interest_paid:.2f}")

def main():
    parser = argparse.ArgumentParser(description="Calculate mortgage repayments and project balance.")
    parser.add_argument("--principal", type=float, required=True, help="Loan principal amount")
    parser.add_argument("--rate", type=float, required=True, help="Annual interest rate (percentage)")
    parser.add_argument("--term", type=int, required=True, help="Loan term in years")
    parser.add_argument("--extra", type=float, default=0, help="Extra monthly payment amount")

    args = parser.parse_args()

    m = Mortgage(args.principal, args.rate, args.term, args.extra)
    m.show_balance_projection()

if __name__ == "__main__":
    main()