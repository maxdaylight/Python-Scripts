# Deploy on Debian / LXC

These steps set up the repository and a shared Python virtual environment for all scripts under `/usr/local/bin/python-scripts`.
Services run as root inside an unprivileged Proxmox LXC.

> Replace `[GITHUB_PAT]` with a valid GitHub Personal Access Token with repo read access.

## 1) Clone repo

```bash
sudo mkdir -p /usr/local/bin
sudo git clone https://maxdaylight:[GITHUB_PAT]@github.com/maxdaylight/python-scripts.git /usr/local/bin/python-scripts
cd /usr/local/bin/python-scripts
```

## 2) Create venv and install dependencies (Python 3.11)

```bash
sudo apt-get update -y
sudo apt-get install -y python3.11-venv python3-pip || sudo apt-get install -y python3-venv python3-pip
# Prefer Python 3.11
python3.11 -m venv /usr/local/bin/python-scripts/venv || python3 -m venv /usr/local/bin/python-scripts/venv
source /usr/local/bin/python-scripts/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Optional: restrict permissions

```bash
sudo chown -R root:root /usr/local/bin/python-scripts
sudo find /usr/local/bin/python-scripts -type d -exec chmod 755 {} \;
sudo find /usr/local/bin/python-scripts -type f -exec chmod 644 {} \;
# Make scripts executable if running directly
sudo find /usr/local/bin/python-scripts -name "*.py" -exec chmod 755 {} \;
```

## 3) Systemd services

Create service files for the scripts. These units run as root in an unprivileged LXC. Adjust `WorkingDirectory` if you clone elsewhere.

`/etc/systemd/system/kraken_oversold.service`:

```ini
[Unit]
Description=Kraken oversold pairs monitor
After=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/usr/local/bin/python-scripts
ExecStart=/usr/local/bin/python-scripts/venv/bin/python /usr/local/bin/python-scripts/CryptoTrading/get_oversold_pairs.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
# Optional email overrides
# Environment=EMAIL_ENABLED=true
# Environment=EMAIL_TO=alerts@example.com

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/kraken_newlistings.service`:

```ini
[Unit]
Description=Kraken new listings monitor
After=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/usr/local/bin/python-scripts
ExecStart=/usr/local/bin/python-scripts/venv/bin/python /usr/local/bin/python-scripts/CryptoTrading/get_new_kraken_assets.py
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kraken_oversold.service kraken_newlistings.service
sudo systemctl status kraken_oversold.service kraken_newlistings.service
```

## 4) Logs

- `journalctl -u kraken_oversold.service -f`
- `journalctl -u kraken_newlistings.service -f`
- File logs: `/var/log/crypto-oversold.log` (fallback `/tmp/crypto-oversold.log`)

Make persistent across reboots (optional):

```bash
sudo sed -i 's/^#\?Storage=.*/Storage=persistent/' /etc/systemd/journald.conf
sudo systemctl restart systemd-journald
```

Create file/state paths (first time only):

```bash
sudo touch /var/log/crypto-oversold.log
sudo mkdir -p /var/lib/kraken_newlistings
```

## 5) Updates (preferred workflow)

```bash
sudo systemctl stop kraken_oversold.service kraken_newlistings.service
cd /usr/local/bin/python-scripts
# Pull with a PAT (read-only). Consider using a credential helper to avoid storing in shell history.
sudo git pull --rebase --autostash
source /usr/local/bin/python-scripts/venv/bin/activate
pip install -r requirements.txt
sudo systemctl start kraken_oversold.service kraken_newlistings.service
```

## 6) Environment and secrets

Use systemd Environment lines or drop-in files to override per host:

```bash
sudo systemctl edit kraken_oversold.service
```

Add, for example:

```ini
[Service]
Environment=EMAIL_ENABLED=true
Environment=EMAIL_TO=maxdaylight@maximized.site
Environment=EMAIL_FROM=stockalerts@maximized.site
Environment=EMAIL_RELAY_HOST=192.168.0.240
Environment=EMAIL_RELAY_PORT=25
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl restart kraken_oversold.service
```

## 7) Troubleshooting

- If `/var/log/crypto-oversold.log` isn’t created, check permissions; script falls back to `/tmp/crypto-oversold.log`.
- Verify venv activation: `which python` should be `/usr/local/bin/python-scripts/venv/bin/python` when running services.
- Use `curl` to test network connectivity to Kraken API endpoints.
