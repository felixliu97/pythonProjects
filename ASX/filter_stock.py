import pandas as pd

def analyze_stocks(file_path):
    # Read the CSV file
    # Handle the dollar signs in the Price column by treating it as a string initially
    df = pd.read_csv(file_path)
    
    # Convert 1yr Return from string percentage to float
    # Remove the % sign and + sign, then convert to float
    df['1yr Return'] = df['1yr Return'].str.replace('%', '').str.replace('+', '').astype(float)
    
    # Convert Franking from string percentage to float
    df['Franking'] = df['Franking'].str.replace('%', '').astype(float)
    
    # Convert Yield from string percentage to float
    df['Yield'] = df['Yield'].str.replace('%', '').astype(float)
    
    # Filter the stocks based on the criteria:
    # DRP = Yes, 1yr Return > 0, Franking = 100%
    filtered_stocks = df[
        (df['DRP'] == 'Yes') & 
        (df['1yr Return'] > 0) & 
        (df['Franking'] == 100.0)
    ]
    
    # Sort by 1yr Return first (descending), then by Yield (descending)
    filtered_stocks = filtered_stocks.sort_values(['1yr Return', 'Yield'], ascending=[False, False])
    
    # Select relevant columns for display
    result = filtered_stocks[['Code', 'Company', 'Price', 'Yield', '1yr Return']]
    
    return result

# File path
file_path = 'market-index-highest-dividend-yield-09-11-2024.csv'

# Analyze stocks
try:
    result = analyze_stocks(file_path)
    
    print("\nStocks matching criteria (DRP=Yes, 1yr Return>0, Franking=100%):")
    print(f"Total matches found: {len(result)}")
    print("=" * 120)
    
    if len(result) > 0:
        # Format the output
        for _, row in result.iterrows():
            print(f"Code: {row['Code']}, Company: {row['Company']}")
            print(f"Price: {row['Price']}, Yield: {row['Yield']:.2f}%, 1 Year Return: +{row['1yr Return']:.2f}%")
            print("-" * 120)
    else:
        print("No stocks found matching the criteria.")
        
except Exception as e:
    print(f"Error: {e}")