#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Load env (optional, for SEARXNG_PROJECT_ROOT etc.)
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Bootstrap venv if missing
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
    "$VENV_DIR/bin/playwright" install chromium
fi

exec "$VENV_DIR/bin/fastmcp" run "$SCRIPT_DIR/server.py"
