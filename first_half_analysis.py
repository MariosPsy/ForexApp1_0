import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.patches as mpatches

# load and preprocess data
def load_data(path):
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['utcTimestampInMinutes'], unit='m')
    df.sort_values('timestamp', inplace=True)
    df.set_index('timestamp', inplace=True)
    df['open'] = df['low'] + df['deltaOpen']
    df['close'] = df['low'] + df['deltaClose']
    df['high'] = df['low'] + df['deltaHigh']
    return df

# υπολογισμός δεικτών σύμφωνα με τη συζήτηση
def calculate_indicators(df):
    # Simple Moving Average (SMA 7)
    df['SMA_7'] = df['close'].rolling(window=7).mean()

    # Exponential Moving Average (EMA 7)
    df['EMA_7'] = df['close'].ewm(span=7, adjust=False).mean()

    # Relative Strength Index (RSI 7 και RSI 14)
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain_7 = gain.rolling(7).mean()
    avg_loss_7 = loss.rolling(7).mean()
    rs_7 = avg_gain_7 / avg_loss_7
    df['RSI_7'] = 100 - (100 / (1 + rs_7))

    avg_gain_14 = gain.rolling(14).mean()
    avg_loss_14 = loss.rolling(14).mean()
    rs_14 = avg_gain_14 / avg_loss_14
    df['RSI_14'] = 100 - (100 / (1 + rs_14))

    # Bollinger Bands με period=7
    mb = df['close'].rolling(window=7).mean()
    msd = df['close'].rolling(window=7).std()
    df['BB_upper'] = mb + (2 * msd)
    df['BB_lower'] = mb - (2 * msd)

    df.dropna(inplace=True)
    return df

def plot_candles_with_indicators(df):
    candle_df = df[['open', 'high', 'low', 'close']].copy()
    apds = [
        mpf.make_addplot(df['SMA_7'], color='blue', width=1),
        mpf.make_addplot(df['EMA_7'], color='orange', width=1),
        mpf.make_addplot(df['BB_upper'], color='grey', linestyle='--'),
        mpf.make_addplot(df['BB_lower'], color='grey', linestyle='--')
    ]
    fig, axes = mpf.plot(
        candle_df,
        type='candle',
        style='charles',
        title='Candles & Indicators (First Half)',
        addplot=apds,
        volume=False,
        figratio=(12, 6),
        figscale=1.2,
        returnfig=True
    )
    # Προσθήκη legend
    custom_lines = [
        mpatches.Patch(color='blue', label='SMA 7'),
        mpatches.Patch(color='orange', label='EMA 7'),
        mpatches.Patch(color='grey', label='Bollinger Bands 7')
    ]
    axes[0].legend(handles=custom_lines, loc='upper left')
    plt.show()

def plot_rsi(df):
    plt.figure(figsize=(12,5))
    plt.plot(df.index, df['RSI_7'], label='RSI 7', color='orange')
    plt.plot(df.index, df['RSI_14'], label='RSI 14', color='blue')
    plt.axhline(70, linestyle='--', color='grey')
    plt.axhline(30, linestyle='--', color='grey')
    plt.title('RSI 7 και RSI 14')
    plt.legend()
    plt.grid(True)
    plt.show()

# main execution
def main():
    df = load_data('trentbars_data.csv')
    mid = len(df) // 2
    first_half = df.iloc[:mid].copy()
    first_half = calculate_indicators(first_half)
    plot_candles_with_indicators(first_half)
    plot_rsi(first_half)
    first_half.to_csv('first_half_indicators.csv')

if __name__ == "__main__":
    main()
