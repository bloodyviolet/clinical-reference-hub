#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3.13}
"$PYTHON" -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip install --only-binary=:all: -r "$ROOT/requirements.lock"
"$ROOT/.venv/bin/python" "$ROOT/scripts/check_dependencies.py"
