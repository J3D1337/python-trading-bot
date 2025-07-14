import ccxt

def test_binance_connection():
    try:
        binance = ccxt.binance()
        markets = binance.load_markets()
        print(f"Connected to Binance. Fetched {len (markets)} markets.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == '__main__':
    test_binance_connection()
