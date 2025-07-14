import ccxt
import pandas as pd
import sys

def fetch_data(symbol='BTC/USDT', timeframe='1h', limit=100):
    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def simple_backtest(df):
    logs = []
    for i in range(2, len(df)):
        if df['close'][i-2] < df['close'][i-1] < df['close'][i]:
            logs.append(f"[BUY] at {df['timestamp'][i]} - Price: {df['close'][i]}")
        elif df['close'][i-2] > df['close'][i-1] > df['close'][i]:
            logs.append(f"[SELL] at {df['timestamp'][i]} - Price: {df['close'][i]}")
    return logs

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USDT'
    timeframe = sys.argv[2] if len(sys.argv) > 2 else '1h'
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    df = fetch_data(symbol, timeframe, limit)
    logs = simple_backtest(df)

    for entry in logs:
        print(entry)
