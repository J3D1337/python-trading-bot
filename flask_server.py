from flask import Flask, request, jsonify
import ccxt
import pandas as pd
import pytz

app = Flask(__name__)

@app.route('/run-bot', methods=['POST'])
def run_bot():
    croatia_tz = pytz.timezone('Europe/Zagreb')
    data = request.get_json()
    symbol = data.get('symbol', 'BTC/USDT')
    timeframe = data.get('timeframe', '1h')
    limit = int(data.get('candle_limit', 1000))
    strategy_list = data.get('strategy', '').upper().split(',')  # e.g. "RSI,MACD"

    try:
        # Fetch data
        binance = ccxt.binance()
        ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(croatia_tz)

        # Precompute indicators
        if 'RSI' in strategy_list:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

        if 'MACD' in strategy_list:
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema12 - ema26
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()

        if 'EMA' in strategy_list:
            df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()

        logs = []

        # Evaluate strategy logic
        for i in range(26, len(df)):  # Start far enough to avoid NaNs
            ts = df['timestamp'][i].strftime('%Y-%m-%d %H:%M:%S')

            # RSI: Cross above 70 = buy, below 30 = sell
            if 'RSI' in strategy_list and 'rsi' in df.columns:
                if df['rsi'][i-1] < 70 and df['rsi'][i] >= 70:
                    logs.append(f"[RSI] BUY signal at {ts} (RSI crossed above 70)")
                elif df['rsi'][i-1] > 30 and df['rsi'][i] <= 30:
                    logs.append(f"[RSI] SELL signal at {ts} (RSI crossed below 30)")

            # MACD: Crossover
            if 'MACD' in strategy_list and 'macd' in df.columns and 'signal' in df.columns:
                if df['macd'][i-1] < df['signal'][i-1] and df['macd'][i] > df['signal'][i]:
                    logs.append(f"[{symbol}] [MACD] BUY crossover at {ts}")
                elif df['macd'][i-1] > df['signal'][i-1] and df['macd'][i] < df['signal'][i]:
                    logs.append(f"[{symbol}] [MACD] SELL crossover at {ts}")

            # EMA: Price cross above/below EMA50
            if 'EMA' in strategy_list and 'ema50' in df.columns:
                if df['close'][i-1] < df['ema50'][i-1] and df['close'][i] > df['ema50'][i]:
                    logs.append(f"[EMA] BUY crossover at {ts} (Price crossed above EMA50)")
                elif df['close'][i-1] > df['ema50'][i-1] and df['close'][i] < df['ema50'][i]:
                    logs.append(f"[EMA] SELL crossover at {ts} (Price crossed below EMA50)")

        return jsonify({'success': True, 'logs': logs})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
