mortgate_input = [
    {
        "loan_amount":1000000,
        "rate":0.04,
        "frequency":"Monthly",
        "years":30
    },
    {
        "loan_amount":1000000,
        "rate":0.04,
        "frequency":"Fortnightly",
        "years":30
    },
    {
        "loan_amount":1000000,
        "rate":0.04,
        "frequency":"Weekly",
        "years":30
    }
]

def get_repayment(loan_amount, rate, frequency, years):
    terms:int

    if frequency == 'Monthly':
        terms = 12
    elif frequency == 'Fortnightly':
        terms = 26
    elif frequency == 'Weekly':
        terms = 52

    repayment_amount = (rate/terms) * (1/(1-(1+rate/terms)**(-years*terms)))*loan_amount
    total_amount_paid = repayment_amount * years * terms

    print(f"Loan amount: {loan_amount}, rate: {rate * 100}%, frequency: {frequency}, years: {years}, Repayment amount: {repayment_amount}, Total ammount paid: {total_amount_paid}")

for i in mortgate_input:
    get_repayment(i['loan_amount'], i['rate'], i['frequency'], i['years'])
