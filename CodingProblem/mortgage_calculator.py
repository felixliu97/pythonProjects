class Mortagage:
    def __init__(self, principal: float, interest_rate: float, term: int, extra_pay: float=0):
        self.principal = principal
        self.interest_rate = interest_rate
        self.term = term
        self.extra_pay = extra_pay

    def calculate_mortgage_repayment(self) -> float:
        monthly_interest_rate = self.interest_rate / 100 / 12
        term_in_months = self.term * 12
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
            balance = balance - repayment - self.extra_pay + (balance * monthly_interest_rate)
            payments_made += 1
            if balance < 1:
                balance = 0
            # print(f"Month {payments_made} - Remaining balance: {balance}")

        total_paid = (repayment + self.extra_pay) * payments_made
        total_interest_paid = total_paid - self.principal
        print(f"Total terms: {payments_made}")
        print(f"Total paid: {total_paid:.2f}, Total interest paid: {total_interest_paid:.2f}")


m1 = Mortagage(750000, 4, 30, 1000)
m1.show_balance_projection()