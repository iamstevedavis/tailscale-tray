#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYINSTALLER_BIN="${PYINSTALLER_BIN:-pyinstaller}"
APP_NAME="tailscale-tray"
ICON_PATH="assets/tailscale-tray.png"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "error: python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

if ! command -v "$PYINSTALLER_BIN" >/dev/null 2>&1; then
  echo "error: pyinstaller not found on PATH" >&2
  echo "hint: $PYTHON_BIN -m pip install --user -r requirements-build.txt" >&2
  exit 1
fi

rm -rf build dist

ARGS=(
  --noconfirm
  --clean
  --specpath build
  --name "$APP_NAME"
  --onefile
  --windowed
  --hidden-import tailscale_status
  app.py
)

if [[ -f "$ICON_PATH" ]]; then
  ARGS=(--icon "$ICON_PATH" "${ARGS[@]}")
fi

"$PYINSTALLER_BIN" "${ARGS[@]}"

echo "Built binary at: $ROOT_DIR/dist/$APP_NAME"
