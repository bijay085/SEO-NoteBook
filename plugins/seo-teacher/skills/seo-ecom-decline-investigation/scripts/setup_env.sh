#!/usr/bin/env bash
# Bootstraps an isolated venv for period_decomposition.py and report_helpers.py.
#
# Why this exists (see references/pitfalls.md #11): system Python in this environment is
# PEP-668 externally-managed — `pip install` at the system level fails with
# "error: externally-managed-environment". This script never touches the system interpreter.
#
# Usage:
#   bash scripts/setup_env.sh [venv_dir]
#   # then run scripts with: <venv_dir>/bin/python scripts/period_decomposition.py ...

set -euo pipefail

VENV_DIR="${1:-.venv}"

echo "Creating venv at: $VENV_DIR"
python3 -m venv "$VENV_DIR"

echo "Installing statistical + reporting stack (binary wheels only — no slow source compiles)..."
"$VENV_DIR/bin/pip" install --only-binary=:all: --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --only-binary=:all: --quiet \
  pandas numpy scipy statsmodels openpyxl pillow requests beautifulsoup4

echo ""
echo "Verifying..."
"$VENV_DIR/bin/python" -c "
import pandas, numpy, scipy, statsmodels, openpyxl, PIL, requests, bs4
print('  pandas      ', pandas.__version__)
print('  numpy       ', numpy.__version__)
print('  scipy       ', scipy.__version__)
print('  statsmodels ', statsmodels.__version__)
print('  openpyxl    ', openpyxl.__version__)
print('  Pillow      ', PIL.__version__)
print('  beautifulsoup4', bs4.__version__)
"

echo ""
echo "Ready. Run scripts with:"
echo "  $VENV_DIR/bin/python scripts/period_decomposition.py <manifest.json>"
echo "  $VENV_DIR/bin/python scripts/live_page_audit.py <page.html>"
