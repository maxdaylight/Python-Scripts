import json
import os
import smtplib
import time
from email.message import EmailMessage

import requests

API_URL = "https://api.kraken.com/0/public/AssetPairs"
STATE_FILE = "/var/lib/kraken_newlistings/seen_pairs.json"
CHECK_INTERVAL = 60  # seconds

# Email configuration (read from env or set here)
EMAIL_ENABLED = True
EMAIL_FROM = "stockalerts@maximized.site"
EMAIL_TO = "maxdaylight@maximized.site"
EMAIL_RELAY_HOST = "192.168.0.240"
EMAIL_RELAY_PORT = 25


def fetch_pairs():
    resp = requests.get(API_URL)
    resp.raise_for_status()
    return set(resp.json()["result"].keys())


def load_seen_pairs():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen_pairs(pairs):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(list(pairs), f)


def send_email(new_pairs):
    msg = EmailMessage()
    msg['Subject'] = "Kraken New Listing Alert"
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg.set_content(
        "New Kraken asset pairs detected:\n\n" +
        "\n".join(new_pairs) +
        "\n\nThis is an automated alert."
    )
    with smtplib.SMTP(EMAIL_RELAY_HOST, EMAIL_RELAY_PORT) as s:
        s.send_message(msg)


def log_new_pairs(new_pairs):
    with open("/var/log/kraken_newlistings.log", "a") as logf:
        for p in new_pairs:
            logf.write(f"{time.ctime()} - NEW PAIR LISTED: {p}\n")
            print(f"[ALERT] New Kraken Pair: {p}")


def main():
    print("Starting Kraken new listing monitor...")
    seen_pairs = load_seen_pairs()
    while True:
        pairs = fetch_pairs()
        new_pairs = pairs - seen_pairs
        if new_pairs:
            log_new_pairs(new_pairs)
            if EMAIL_ENABLED:
                send_email(new_pairs)
            seen_pairs |= new_pairs
            save_seen_pairs(seen_pairs)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
