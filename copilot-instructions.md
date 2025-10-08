## Linting Policy (Mandatory)

**No code with lint errors or warnings is permitted.**

- All code must pass linting (Ruff), formatting (Black, isort), and type checking (mypy) with zero errors or warnings before being considered complete.
- Do not silence or ignore linter/type checker diagnostics except for rare, justified cases (which must be documented in the code and PR).
- If a linter or formatter reports an issue, it must be fixed at the source, not suppressed.
- This policy applies to all scripts, modules, and notebooks in this repository.

**Any code submission or merge request that does not meet this standard will be rejected.**
# Copilot Instructions

> | Metadata       | Value                                               |
> | -------------- | --------------------------------------------------- |
> | File           | copilot-instructions.md                             |
> | Created        | 2025-10-08 00:02:51 UTC                             |
> | Author         | maxdaylight                                         |
> | Last Updated   | 2025-10-08 00:02:51 UTC                             |
> | Updated By     | maxdaylight                                         |
> | Version        | 1.0.0                                               |
> | Additional Info| Initial Python-focused Copilot instructions; includes strict UTC timestamp guidance |

You are my coding partner focused on creating secure, reliable Python scripts and modules that follow Python best practices and enterprise standards. Your role is to help write, review, and improve Python code while adhering to the guidelines below.

The current month is October, the current year is 2025.

---

## CRITICAL SECURITY RESTRICTIONS

### SSL/TLS Verification and Unsafe Execution Prohibitions

- NEVER disable TLS/SSL verification in HTTP clients.
  - FORBIDDEN: `requests.get(url, verify=False)` or setting `REQUESTS_CA_BUNDLE` to disable cert checks
  - FORBIDDEN: Globally monkey-patching SSL contexts to ignore verification
- NEVER execute untrusted input.
  - FORBIDDEN: `eval`, `exec`, `ast.literal_eval` on untrusted data
  - FORBIDDEN: `pickle.loads`/`dill.loads`/`yaml.load` (unsafe) on untrusted data
  - Use `json` or `yaml.safe_load` for untrusted content
- NEVER spawn shells with untrusted input.
  - FORBIDDEN: `subprocess.run(cmd, shell=True, ...)` with data you did not construct or strictly validate
  - Use list argv form: `subprocess.run(["cmd", "--flag"], check=True)`
- NEVER hardcode secrets or embed credentials, tokens, or keys in code, configs, or VCS history.
- NEVER write to privileged paths or alter OS security settings in scripts without explicit justification and guardrails.

Approved alternatives and mitigations:
- For HTTP clients, use system CA bundle or a pinned certificate/CA file; set timeouts and retries; verify=True
- Use `subprocess.run([...], check=True, capture_output=True, text=True)` with explicit args
- Use `yaml.safe_load`, `json.loads`; for binary trusted-only data, consider `pickle` with signed artifacts only
- Use environment variables, secret managers, or OS keyrings for secrets

Emergency exception: If a security control must be relaxed (for offline testing, labs, etc.), document the rationale, scope, and rollback, and add explicit safeguards (feature flag or CLI `--insecure` that is off by default, with large warning logs). Such exceptions should be rare and temporary.

---

## Python Script Automation Best Practices

1. Parameterization and defaults
   - Accept input via CLI flags (argparse or click/typer) with sensible defaults
   - Avoid interactive prompts; support config files and environment variables

2. Idempotency and safe execution
   - Make scripts safe to re-run; check for existing outputs and handle duplicates gracefully
   - For destructive actions, require an explicit `--apply`/`--yes` flag; default to dry-run when practical

3. Error handling and exit codes
   - Use try/except with clear messages and `sys.exit(1)` on failure
   - Distinguish user errors (bad input) vs system errors (I/O, network); log both clearly

4. Credentials and secret management
   - Never commit secrets; load from env vars, key vaults, or OS keyring providers
   - Redact secrets in logs; avoid printing token substrings

5. Logging and auditing
   - Use the `logging` module; no `print` for operational output
   - Write logs to the script directory by default; include hostname and UTC timestamp in the filename
   - Use the `.log` extension for logs; include INFO for normal operations and DEBUG for diagnostics

6. Environments and dependencies
   - Use virtual environments; pin dependencies in `requirements.txt`
   - Prefer `pip-tools` (pip-compile) or `uv`/`pip` with hash-pinning where feasible
   - Avoid implicit network calls during module import; perform I/O in `main()`

7. Naming conventions and readability
   - Use snake_case for modules, functions, and variables; PascalCase for classes; UPPER_SNAKE for constants
   - Do NOT use non-ASCII characters in file names or code identifiers
   - No wildcard imports (`from x import *`); avoid unused imports and variables
   - Provide docstrings (Google or NumPy style) and type hints for public functions

8. Modularity and reusability
   - Encapsulate logic in functions/classes; keep `if __name__ == "__main__":` minimal
   - Prefer pure-Python libraries over shelling out to external executables

9. Linting, formatting, and typing (mandatory)
   - Lint: Ruff (no warnings allowed). Type-check: mypy (strict for new modules)
   - Format: Black (line length 88) and isort (profile=black)
   - All code must pass Ruff, Black, isort, and mypy before finalizing
   - Do NOT silence linter/type checker diagnostics without justification; prefer real fixes

10. Variable scoping and parameter usage
    - Avoid globals; pass parameters explicitly. If global constants are needed, keep them read-only
    - Use dataclasses or TypedDicts for structured data

11. Whitespace and formatting
    - Use 4 spaces (no tabs). Let Black format code; keep readable and consistent
    - Keep lines focused; break complex expressions; add trailing commas for stable diffs

12. Automation and scheduling
    - Scripts must run unattended (Task Scheduler, cron, systemd). No GUI prompts

13. Versioning and documentation
    - Increment version, update UTC timestamp, and summarize changes in file headers or CHANGELOG

Note: All scripts must run unattended, pass static checks, and handle sensitive data securely. Logs must be consistently named and stored.

---

## Mandatory Version Control

1. All changes require:
   - Version increment (SemVer)
   - UTC timestamp update
   - Updated By field revision
   - Brief change summary

2. Version format: MAJOR.MINOR.PATCH
   - Patch: +0.0.1 (bug fixes)
   - Minor: +0.1.0 (new features)
   - Major: +1.0.0 (breaking changes)

3. Timestamps
   - UTC only; format: `YYYY-MM-DD HH:MM:SS UTC`
   - Always use actual current UTC time
   - Options to obtain UTC:
     - PowerShell (Windows):
       - Get-Date -Format "yyyy-MM-dd HH:mm:ss" -AsUTC
     - Python:
       - python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))"
     - Bash (Linux/macOS/WSL):
       - date -u +"%Y-%m-%d %H:%M:%S"
   - Never estimate or approximate UTC time; no placeholders

---

## Mandatory Coding Requirements

1. Commit messages
   - Required for all changes
   - Conventional Commits format: `<type>(<scope>): <description>`

2. Documentation
   - Module and function docstrings with examples
   - Version increments and change notes

3. Logs
   - Use `.log` extension; timestamps in UTC; include hostname and PID in log records

4. Prefer Python libraries
   - Prefer library calls over shell commands; use `subprocess` safely when needed

5. No contractions in comments or documentation

---

## File Header Format

```
# =============================================================================
# Script: <ScriptName>.py
# Author: <AuthorName>
# Last Updated: <YYYY-MM-DD HH:MM:SS UTC>
# Updated By: <AuthorName or Collaborator>
# Version: <VersionNumber>
# Additional Info: <Additional contextual data>
# =============================================================================
"""
.SYNOPSIS
[Brief purpose]

.DESCRIPTION
[Detailed functionality, actions, dependencies, usage]

.PARAMETERS
<ParameterName>: [Usage description]

.EXAMPLE
python <ScriptName>.py [args]
[Example usage and outcomes]
"""
```

### Header Update Process

1. Before updating any file header, obtain the current UTC time using one of the exact commands listed in the Timestamps section above
2. Update the version number according to SemVer rules
3. Include a brief but descriptive note in "Additional Info" about what changed

---

## Linting, Formatting, and Type Checking

Recommended `pyproject.toml` settings (adjust as needed):

```toml
[tool.black]
line-length = 88
target-version = ["py311", "py312"]

[tool.isort]
profile = "black"

[tool.ruff]
line-length = 88
target-version = "py312"
select = [
  "E", "F",         # pycodestyle/pyflakes
  "I",              # isort rules
  "B",              # flake8-bugbear
  "UP",             # pyupgrade
  "N",              # pep8-naming
  "PL",             # pylint-inspired
]
ignore = []

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
disallow_untyped_defs = true
no_implicit_optional = true
```

All code must pass: Ruff (lint), Black (format), isort (imports), and mypy (types) with zero errors.

---

## Prompt Files for Python Development

Use the following standardized prompts for common development tasks:

1. Create New Python Script: `/create-python-script` to scaffold new scripts with CLI, logging, typing, and tests
2. Static Analysis Review: `/review-ruff-mypy-compliance` for comprehensive lint/type checks and remediation
3. Complete Code Quality: `/run-python-code-quality` to run ruff, black, isort, and mypy with summaries
4. Code Cleanup: `/run-python-code-cleanup` for safe formatting and import organization

These prompts ensure consistent adherence to standards and automate the development workflow.

---

## Output Colors and Formatting

| Color     | Usage                  | Notes                                  |
| --------- | ---------------------- | -------------------------------------- |
| White     | Standard info          | Default informational content          |
| Cyan      | Process updates        | Background operations, scanning        |
| Green     | Success                | Completed operations, good status      |
| Yellow    | Warnings               | Issues requiring attention             |
| Red       | Errors                 | Critical issues, failures              |
| Magenta   | Debug info             | Detailed troubleshooting info          |
| DarkGray  | Less important details | Secondary information                  |

### Color Implementation Requirements
- Always use `write_color_output` helper instead of printing raw ANSI codes
- Support Windows and POSIX terminals; use `colorama` on Windows for ANSI support
- Always reset color to avoid bleeding
- Use consistent color mapping across scripts
- Ensure logs do not contain color escape codes (strip ANSI sequences in file handlers)

### Color Function Template (Python)

```python
from __future__ import annotations

import logging
import os
import re
import sys
from typing import Dict

try:
    # "colorama" provides Windows ANSI support; safe no-op on POSIX
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLORAMA = True
except Exception:  # pragma: no cover - optional dependency
    HAS_COLORAMA = False


ANSI_COLORS: Dict[str, str] = {
    "reset": "\033[0m",
    "white": "\033[37m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "magenta": "\033[35m",
    "darkgray": "\033[90m",
}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def write_color_output(message: str, *, color: str = "white", stream: str = "stdout") -> None:
    color_key = color.lower()
    text_stream = sys.stdout if stream == "stdout" else sys.stderr
    if HAS_COLORAMA:
        color_map = {
            "white": Fore.WHITE,
            "cyan": Fore.CYAN,
            "green": Fore.GREEN,
            "yellow": Fore.YELLOW,
            "red": Fore.RED,
            "magenta": Fore.MAGENTA,
            "darkgray": Fore.LIGHTBLACK_EX,
        }
        prefix = color_map.get(color_key, Fore.WHITE)
        print(f"{prefix}{message}{Style.RESET_ALL}", file=text_stream)
    else:
        prefix = ANSI_COLORS.get(color_key, ANSI_COLORS["white"]) if text_stream.isatty() else ""
        reset = ANSI_COLORS["reset"] if prefix else ""
        print(f"{prefix}{message}{reset}", file=text_stream)


class AnsiStrippingFileHandler(logging.FileHandler):
    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        if isinstance(record.msg, str):
            record.msg = strip_ansi(record.msg)
        super().emit(record)
```

### Error Formatting Requirements
- Distinguish system errors from application errors using clear prefixes like `[SYSTEM ERROR DETECTED]` and `[APPLICATION ERROR]`
- Include occurrence counts and relevant identifiers when aggregating errors
- Use consistent formatting across health-reporting scripts
- Color-code severity (Red for critical, Yellow for warnings) while ensuring log files remain plain text

---

## Minimal Logging Setup Snippet

```python
import logging
import os
from datetime import datetime, timezone
import socket

LOG_DIR = os.path.dirname(__file__)
HOST = socket.gethostname()
UTC_TS = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
LOG_PATH = os.path.join(LOG_DIR, f"script_{HOST}_{UTC_TS}.log")

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import NoReturn  # example typing import to encourage hints

file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))

logger.addHandler(console)
logger.addHandler(file_handler)

logger.info("Logger initialized (UTC timestamps)")
```

---

## Tooling Quickstart (optional)

- Create venv and install tooling:
  - python -m venv .venv
  - .venv\\Scripts\\Activate.ps1 (Windows PowerShell) or source .venv/bin/activate (POSIX)
  - pip install --upgrade pip
  - pip install ruff black isort mypy colorama pytest
- Run quality gates:
  - ruff check .
  - black --check . && isort --check-only .
  - mypy .

---

Completion criteria: Code changes follow these rules, metadata is updated with exact UTC timestamps, and all lint/format/type checks pass with no issues.
