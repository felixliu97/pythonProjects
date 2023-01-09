def tax_rate(taxable_income: float):
    tax_amount, tax_rate = 0, 0
    assert(taxable_income >= 0)
    # Nil up to $18200
    if taxable_income <= 18200:
        pass
    # 19 cents for each $1 over $18,200
    elif taxable_income <= 45000:
        tax_amount = (taxable_income - 18200) * 0.19
    # $5,092 plus 32.5 cents for each $1 over $45,000
    elif taxable_income <= 120000:
        tax_amount = 5092 + (taxable_income - 45000) * 0.325
    # $29,467 plus 37 cents for each $1 over $120,000
    elif taxable_income <= 180000:
        tax_amount = 29467 + (taxable_income - 120000) * 0.37
    # $51,667 plus 45 cents for each $1 over $180,000
    else:
        tax_amount = 51667 + (taxable_income - 180000) * 0.45

    tax_rate = tax_amount / taxable_income if taxable_income != 0 else 0
    print(f"taxable income: {taxable_income}, tax amount: {tax_amount} tax rate: {tax_rate:.3f}")

for income in range (0, 300001, 5000):
    tax_rate(income)