import concurrent.futures

import pandas as pd
import pandas_ta as ta
import requests


def get_asset_pairs():
    # Tickers to exclude as base asset
    exclude_bases = {
        "USD", "USDT", "USDC", "EUR", "GBP",
        "DAI", "CHF", "CAD", "JPY", "TRY",
        "TUSD", "USDD", "UUSD", "GUSD"
    }
    resp = requests.get("https://api.kraken.com/0/public/AssetPairs")
    data = resp.json()
    pairs = []
    for k, v in data["result"].items():
        altname = v.get("altname", "")
        wsname = v.get("wsname", "")
        base = v.get("base", "")
        quote = v.get("quote", "")

        # Only pairs with USD quote
        if (
            quote.replace("Z", "").replace("X", "") == "USD"
            or altname.endswith("USD")
        ):
            # Extract actual base ticker (strip X/Z for Kraken format)
            base_ticker = base.replace("X", "").replace("Z", "")

            # Double check base asset is not excluded (stablecoin/fiat)
            # Also check wsname (e.g. "USDT/USD", "EUR/USD")
            if (
                base_ticker not in exclude_bases
                and not any(wsname.startswith(b + "/") for b in exclude_bases)
            ):
                pairs.append(k)
    return pairs


def is_rebound_candidate(pair):
    ticker = requests.get(
        f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    ).json()['result']
    info = next(iter(ticker.values()))
    volume_24h = float(info['v'][1])
    last_price = float(info['c'][0])
    # Only consider pairs with last_price between $1 and $500
    if not (1 < last_price < 500):
        return False
    # Only pairs with volume > 100000
    return volume_24h > 100000


def get_ohlc(pair, interval=15):
    resp = requests.get(
        f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    )
    data = resp.json()["result"]
    ohlc = next(iter([v for v in data.values() if isinstance(v, list)]))
    df = pd.DataFrame(
        ohlc,
        columns=[
            "time", "open", "high", "low", "close", "vwap", "volume", "count"
        ],
    )
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    return df


def analyze(pair, interval):
    df = get_ohlc(pair, interval=interval)
    if len(df) < 14:
        return None
    rsi = ta.rsi(df["close"], length=14)
    stoch = ta.stoch(df["high"], df["low"], df["close"], k=14, d=3)
    latest_rsi = rsi.iloc[-2] if len(rsi) >= 2 else None
    latest_stoch_k = (
        stoch["STOCHk_14_3_3"].iloc[-2] if len(stoch) >= 2 else None
    )
    # Rolling support check
    recent_low = df['close'].rolling(window=90).min().iloc[-2]
    last_price = df['close'].iloc[-2]
    near_support = last_price <= recent_low * 1.07
    # Oversold and candidate for rebound
    if latest_rsi is not None and latest_stoch_k is not None:
        if latest_rsi < 30 and latest_stoch_k < 20:
            if is_rebound_candidate(pair) and near_support:
                return pair, latest_rsi, latest_stoch_k
    return None


def main():
    pairs = get_asset_pairs()
    oversold_coins = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_pair = {
            executor.submit(analyze, pair, 15): pair
            for pair in pairs
        }
        for future in concurrent.futures.as_completed(future_to_pair):
            result = future.result()
            if result:
                oversold_coins.append(result)
    print('Oversold coins:')
    for coin, rsi, stoch in oversold_coins:
        print(f'{coin}: RSI={rsi:.2f}, StochK={stoch:.2f}')


if __name__ == "__main__":
    main()
