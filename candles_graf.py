import pandas as pd
import mplfinance as mpf

# Φόρτωση δεδομένων
df = pd.read_csv("trentbars_data.csv")

# Μετατροπή UTC timestamp σε datetime αντικείμενο
df["timestamp"] = pd.to_datetime(df["utcTimestampInMinutes"], unit="m")

# Ταξινόμηση κατά ημερομηνία
df.sort_values("timestamp", inplace=True)

# Επαναφορά index
df.reset_index(drop=True, inplace=True)

# Υπολογισμός πραγματικών τιμών
df["open"] = df["low"] + df["deltaOpen"]
df["close"] = df["low"] + df["deltaClose"]
df["high"] = df["low"] + df["deltaHigh"]

df_candle = df[["timestamp", "open", "high", "low", "close"]].copy()
df_candle.set_index("timestamp", inplace=True)

mpf.plot(df_candle, type='candle', style='charles', title='EUR/USD - 2024', volume=False)