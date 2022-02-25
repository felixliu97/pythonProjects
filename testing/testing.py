from numpy import result_type
import pandas as pd
import re
import datetime

def transform(fusion):
    values = values = re.findall(r'^.* (\d+/\d+/\d+) (\w+)\((\d+):(\d+)\)$', fusion)
    return ' '.join(values[0])

df = pd.DataFrame({'fusion': ['WC 7/01/2020 Metro(1:2020)']})
df[['a','b','c','d']] = df['fusion'].apply(transform).str.split(expand=True)
df['e'] = "1,000,000"
df['e'] = df['e'].str.replace(',', '')
df['f'] = '2.5%'
df['f'] = df['f'].astype(str).str.replace('%', '')
df['a'] = pd.to_datetime(df['a'])
df['g'] = '"' + df['f'] + '"'
df.drop(['fusion'], axis=1, inplace=True)
print(f"df:{df.head(5)}")