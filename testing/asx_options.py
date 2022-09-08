from bs4 import BeautifulSoup
import requests
import pandas as pd

# Real Estates
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

url = 'https://rosser.com.au/options.htm'
response = requests.get(url, headers = headers)

soup = BeautifulSoup(response.text, 'html.parser')

stocks_table = soup.find('table')

df = pd.read_html(str(stocks_table))[0]

# print(f"Columns: {df.columns}")

df = df[(df['Exercise'] + df['Opt Price'] < df['Share Price']) & df['Exercise'] > 0]
df['diff'] = df['Share Price'] - df['Exercise'] - df['Opt Price']

print(df)
