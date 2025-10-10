import concurrent.futures
import logging
import smtplib
from email.message import EmailMessage
from logging.handlers import TimedRotatingFileHandler

import pandas as pd
import requests
from ta.momentum import (
    RSIIndicator,
    StochasticOscillator,
)

# Email configuration (read from env or set here)
EMAIL_ENABLED = True
EMAIL_FROM = "stockalerts@maximized.site"
EMAIL_TO = "maxdaylight@maximized.site"
EMAIL_RELAY_HOST = "192.168.0.240"
EMAIL_RELAY_PORT = 25

# Logging configuration
LOG_FILE = "/var/log/crypto-oversold.log"
LOG_ROTATE_INTERVAL_HOURS = 168  # 7 days


def setup_logger():
    """Configure a logger that writes to a rotating file every 168 hours
    and also to stdout (captured by journald when run as a service)."""
    logger = logging.getLogger("kraken_oversold")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # Try primary log path; on failure, fall back to CWD
    try:
        file_handler = TimedRotatingFileHandler(
            LOG_FILE,
            when="h",
            interval=LOG_ROTATE_INTERVAL_HOURS,
            backupCount=8,
            encoding="utf-8",
        )
    except (PermissionError, FileNotFoundError, OSError):
        # Fall back to a safe, non-repo location to avoid
        # modifying the git workspace
        fallback = "/tmp/crypto-oversold.log"
        file_handler = TimedRotatingFileHandler(
            fallback,
            when="h",
            interval=LOG_ROTATE_INTERVAL_HOURS,
            backupCount=8,
            encoding="utf-8",
        )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)
    return logger


logger = setup_logger()


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


def min_breakeven_move(entry, maker_fee=0.002, taker_fee=0.0035):
    rt_fee = maker_fee + taker_fee
    return rt_fee + 0.001  # Add 0.1% buffer for slippage/execution


def analyze(pair, interval, maker_fee=0.002, taker_fee=0.0035):
    df = get_ohlc(pair, interval=interval)
    if len(df) < 20:
        return None, ["insufficient_data"]
    try:
        rsi_series = RSIIndicator(close=df["close"], window=14).rsi()
        stoch_k_series = (
            StochasticOscillator(
                high=df["high"],
                low=df["low"],
                close=df["close"],
                window=14,
                smooth_window=3,
            ).stoch()
        )
    except Exception:
        rsi_series = pd.Series(dtype=float)
        stoch_k_series = pd.Series(dtype=float)
    latest_rsi = rsi_series.iloc[-2] if len(rsi_series) >= 2 else None
    latest_stoch_k = (
        stoch_k_series.iloc[-2] if len(stoch_k_series) >= 2 else None
    )

    entry = df["close"].iloc[-2]           # Likely fill price
    target = df["close"].rolling(20).mean().iloc[-2]  # Mean reversion (MA 20)
    min_move_pct = min_breakeven_move(entry, maker_fee, taker_fee)
    actual_move_pct = (target - entry) / entry

    # Rolling support check
    recent_low = df['close'].rolling(window=90).min().iloc[-2]
    last_price = entry
    near_support = last_price <= recent_low * 1.07

    fail_reasons = []
    if latest_rsi is None or latest_stoch_k is None:
        fail_reasons.append("no_rsi_or_stoch")
    else:
        if latest_rsi >= 30:
            fail_reasons.append(f"rsi={latest_rsi:.2f} not < 30")
        if latest_stoch_k >= 20:
            fail_reasons.append(f"stoch_k={latest_stoch_k:.2f} not < 20")
        if not is_rebound_candidate(pair):
            fail_reasons.append("not_rebound_candidate")
        if not near_support:
            fail_reasons.append("not_near_support")
        if actual_move_pct <= min_move_pct:
            fail_reasons.append(

                    f"move={actual_move_pct*100:.2f}% <= "
                    f"min_required={min_move_pct*100:.2f}%"

            )
        if (
            latest_rsi < 30
            and latest_stoch_k < 20
            and is_rebound_candidate(pair)
            and near_support
            and actual_move_pct > min_move_pct
        ):
            return {
                "pair": pair,
                "entry": entry,
                "target": target,
                # Example: half the target range for stop
                "stop": entry - (target - entry) / 2,
                "rsi": latest_rsi,
                "stoch_k": latest_stoch_k,
                "expected_pct": round(
                    actual_move_pct * 100, 2
                ),
            }, None
    return None, fail_reasons


def send_email(good_trades):
    if not good_trades:
        return
    msg = EmailMessage()
    msg['Subject'] = "Kraken Oversold Pairs Alert"
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    lines = [
        "Oversold Kraken USD pairs detected (mean reversion candidates):",
        "",
    ]
    for t in good_trades:
        lines.append(
            f"{t['pair']}: Entry={t['entry']:.4f}, "
            f"Target={t['target']:.4f}, Stop={t['stop']:.4f}, "
            f"Expected Move={t['expected_pct']}%, "
            f"RSI={t['rsi']:.2f}, StochK={t['stoch_k']:.2f}"
        )
    lines.append("")
    lines.append("This is an automated alert.")
    msg.set_content("\n".join(lines))
    try:
        with smtplib.SMTP(EMAIL_RELAY_HOST, EMAIL_RELAY_PORT) as s:
            s.send_message(msg)
        logger.info(
            "Email sent to %s with %d oversold candidates.",
            EMAIL_TO,
            len(good_trades),
        )
    except Exception as e:
        logger.error("Failed to send email: %s", e)


def main():
    logger.info("Starting Kraken oversold pairs monitor run...")
    pairs = get_asset_pairs()
    logger.info("Fetched %d USD pairs for analysis.", len(pairs))
    good_trades = []
    near_misses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_pair = {
            executor.submit(analyze, pair, 15): pair for pair in pairs
        }
        for future in concurrent.futures.as_completed(future_to_pair):
            result, fail_reasons = future.result()
            if result:
                good_trades.append(result)
            elif fail_reasons:
                near_misses.append((future_to_pair[future], fail_reasons))
    print('Profitable Reversion Trades:')
    logger.info('Profitable Reversion Trades:')
    if good_trades:
        for trade in good_trades:
            print(
                f"{trade['pair']}: Entry={trade['entry']:.2f}, "
                f"Target={trade['target']:.2f}, "
                f"Stop={trade['stop']:.2f}, "
                f"Expected Move={trade['expected_pct']}%, "
                f"RSI={trade['rsi']:.2f}, "
                f"StochK={trade['stoch_k']:.2f}"
            )
            logger.info(
                (
                    "%s: Entry=%.2f, Target=%.2f, Stop=%.2f, "
                    "Expected Move=%s%%, RSI=%.2f, StochK=%.2f"
                ),
                trade['pair'], trade['entry'], trade['target'], trade['stop'],
                trade['expected_pct'], trade['rsi'], trade['stoch_k']
            )
        if EMAIL_ENABLED:
            send_email(good_trades)
    else:
        print('No Profitable Reversion Trades Found!')
        logger.info('No Profitable Reversion Trades Found!')
    if near_misses:
        print('\nNear Misses:')
        logger.info('Near Misses:')
        for pair, reasons in near_misses:
            print(f"{pair}: Failed criteria -> {', '.join(reasons)}")
            logger.info("%s: Failed criteria -> %s", pair, ', '.join(reasons))


if __name__ == "__main__":
    main()
