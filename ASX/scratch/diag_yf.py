import yfinance as yf
from scripts.utils import ticker_to_ax

symbols = ['VKA.AX', 'CYM.AX']
df_all = yf.download(symbols, period='1mo', interval='1d', progress=False, group_by='ticker')

print(f"Columns: {df_all.columns}")
print(f"Levels: {df_all.columns.levels}")

for s in symbols:
    if s in df_all.columns.levels[0]:
        print(f"{s} found in levels[0]")
        df_s = df_all[s]
        print(f"{s} last close: {df_s['Close'].iloc[-1]}")
    else:
        print(f"{s} NOT found in levels[0]")
