from numpy import result_type
import pandas as pd
import re
import datetime

def transform(fusion):
    values = re.findall(r'^.* (\d+/\d+/\d+) (\w+)\((\d+):(\d+)\)$', fusion)
    print(values)
    return '|'.join(values[0])

df = pd.DataFrame({'fusion': ['WC 7/01/2020 Metro(1:2020)']})
df[['a','b','c','d']] = df['fusion'].apply(transform).str.split('|',expand=True)
df['e'] = "1,000,000"
df['e'] = df['e'].str.replace(',', '')
df['f'] = '2.5%'
df['f'] = df['f'].astype(str).str.replace('%', '')
df['a'] = pd.to_datetime(df['a'])
df['g'] = '"' + df['f'] + '"'
if 'fusion1' in df:
    df.drop(['fusion1'], axis=1, inplace=True)
print(f"df:{df.head(5)}")


s = "s3://bucket/folder/file (ghi abc). CSV"
ret = re.findall(r'\((.*)\)', s)
str = ret[0] if ret else ''
print(str)