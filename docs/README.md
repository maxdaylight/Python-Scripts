# Python Scripts

A collection of small utilities and trading tools. Production deployments use a dedicated Python virtual environment to isolate dependencies. Services run as root inside an unprivileged Proxmox LXC.

## Layout

- `CryptoTrading/`
  - `get_oversold_pairs.py` — scans Kraken USD pairs for oversold mean-reversion setups and emails alerts.
  - `get_new_kraken_assets.py` — monitors Kraken for new trading pairs and emails alerts.
- `utils.py` — shared helpers (if any)
- `requirements.txt` — pinned dependencies for server installs
- `pyproject.toml` — local packaging and tooling (optional)
- `docs/` — this documentation

## Python virtual environment (Python 3.11)

We standardize on a single venv on servers at (Python 3.11 preferred):

```bash
/usr/local/bin/python-scripts/venv
```

Activate it:

```bash
source /usr/local/bin/python-scripts/venv/bin/activate
```

Local development (Windows/PowerShell):

```bash
. .\.venv\Scripts\Activate.ps1
```

## Quick start (local)

1. Create and activate a venv
2. Install requirements
3. Run a script

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell: . .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python CryptoTrading/get_oversold_pairs.py
```

## Email and logs

- Email alerts use an SMTP relay, configured inside each script (`EMAIL_*` variables). On servers, you can override with environment variables via systemd.
- Logs: scripts write to `/var/log/crypto-oversold.log` or fall back to `/tmp/crypto-oversold.log`. Use `journalctl -u <service>` for service logs.

## Updates on server (preferred)

1) Stop services
2) Pull latest code (PAT-only, read access)
3) Activate venv and install requirements
4) Start services

```bash
sudo systemctl stop kraken_oversold.service kraken_newlistings.service
cd /usr/local/bin/python-scripts
sudo git pull --rebase --autostash
source /usr/local/bin/python-scripts/venv/bin/activate
pip install -r requirements.txt
sudo systemctl start kraken_oversold.service kraken_newlistings.service
```

See deployment details in `docs/deployment-debian.md`.

## Contributing

- Use feature branches and PRs
- Keep runtime artifacts out of the repo (logs, caches, service files)
- Add minimal docs for any new script
