import pandas as pd

# Read the CSV file into a DataFrame
df = pd.read_csv('market-index-highest-dividend-yield-09-11-2024.csv')

# Display the first few rows of the DataFrame
print("Original DataFrame:")
print(df.head())

# # Display basic information about the DataFrame
# print("\nDataFrame Info:")
# print(df.info())

# Perform some filtering operations

# # 1. Filter rows based on a condition
# filtered_df = df[df['Price'] > 3.0]
# print("\nFiltered DataFrame (Price > 3.0):")
# print(filtered_df)

# # 2. Select specific columns
# selected_columns = ['Code', 'Company', 'Price', 'Yield']
# selected_df = df[selected_columns]
# print("\nSelected Columns:")
# print(selected_df)

# # 3. Sort the DataFrame by a column
# sorted_df = df.sort_values('Yield', ascending=False)
# print("\nSorted by Yield (Descending):")
# print(sorted_df)

# # 4. Filter rows with multiple conditions
# multi_condition_df = df[(df['Franking'] == '100%') & (df['DRP'] == 'Yes')]
# print("\nFiltered with multiple conditions (100% Franking and DRP available):")
# print(multi_condition_df)

# # 5. Calculate some statistics
# print("\nStatistics:")
# print(df['Yield'].describe())

# # 6. Group by a column and calculate mean
# grouped_df = df.groupby('Franking')['Yield'].mean()
# print("\nMean Yield grouped by Franking:")
# print(grouped_df)

# # Save the filtered DataFrame to a new CSV file
# filtered_df.to_csv('filtered_data.csv', index=False)
# print("\nFiltered data saved to 'filtered_data.csv'")