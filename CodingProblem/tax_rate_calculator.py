def tax_rate(taxable_income: float):
    tax_amount = 0.0
    assert(taxable_income >= 0)
    
    # 2024-2025+ Resident Tax Rates (Revised Stage 3 Cuts)
    # 0 – $18,200: Nil
    # $18,201 – $45,000: 16%
    # $45,001 – $135,000: 30%
    # $135,001 – $190,000: 37%
    # $190,001+: 45%
    
    if taxable_income <= 18200:
        pass
    elif taxable_income <= 45000:
        tax_amount = (taxable_income - 18200) * 0.16
    elif taxable_income <= 135000:
        tax_amount = 4288 + (taxable_income - 45000) * 0.30
    elif taxable_income <= 190000:
        tax_amount = 31288 + (taxable_income - 135000) * 0.37
    else:
        tax_amount = 51638 + (taxable_income - 190000) * 0.45

    current_tax_rate = tax_amount / taxable_income if taxable_income != 0 else 0
    take_home_pay = taxable_income - tax_amount
    print(f"taxable income: {taxable_income}, tax amount: {tax_amount:.2f} take home pay: {take_home_pay:.2f} tax rate: {current_tax_rate*100:.2f}%")

def main():
    for income in range(0, 300001, 5000):
        tax_rate(income)

if __name__ == "__main__":
    main()