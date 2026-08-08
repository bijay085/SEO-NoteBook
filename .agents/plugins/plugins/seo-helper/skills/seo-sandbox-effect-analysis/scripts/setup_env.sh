#!/usr/bin/env bash
# setup_env.sh : OPTIONAL. The core scripts (sandbox_metrics / entity / backlink / live_verify)
# are pure stdlib and need NO venv. This only matters for:
# - report_helpers.py -> needs `openpyxl`
# - reading .xlsx GSC exports directly -> needs `openpyxl` (or convert to CSV first)
# This environment's system Python is PEP-668 managed, so `pip install` at system level fails.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q openpyxl
echo "venv ready: $VENV (run scripts with $VENV/bin/python)"
