#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="${1:-0.1.0}"
ITERATION="${ITERATION:-1}"
ARCH="${ARCH:-$(uname -m)}"
FPM_BIN="${FPM_BIN:-fpm}"
APP_NAME="tailscale-tray"
PKGROOT="$ROOT_DIR/pkgroot"
DESKTOP_FILE="packaging/tailscale-tray.desktop"
ICON_SOURCE_PNG="assets/tailscale-tray.png"
ICON_SOURCE_SVG="assets/tailscale-tray.svg"

if ! command -v "$FPM_BIN" >/dev/null 2>&1; then
  echo "error: fpm not found on PATH" >&2
  echo "hint: sudo dnf install -y ruby ruby-devel gcc make && sudo gem install fpm" >&2
  exit 1
fi

if [[ ! -x "dist/$APP_NAME" ]]; then
  echo "error: dist/$APP_NAME not found. Run ./scripts/build-binary.sh first." >&2
  exit 1
fi

if [[ ! -f "$DESKTOP_FILE" ]]; then
  echo "error: missing desktop file: $DESKTOP_FILE" >&2
  exit 1
fi

if command -v desktop-file-validate >/dev/null 2>&1; then
  desktop-file-validate "$DESKTOP_FILE"
fi

rm -rf "$PKGROOT"
rm -f "$ROOT_DIR/$APP_NAME-$VERSION"-*.rpm
mkdir -p \
  "$PKGROOT/usr/bin" \
  "$PKGROOT/usr/share/applications" \
  "$PKGROOT/usr/share/icons/hicolor/256x256/apps" \
  "$PKGROOT/usr/share/icons/hicolor/scalable/apps"

install -m 0755 "dist/$APP_NAME" "$PKGROOT/usr/bin/$APP_NAME"
install -m 0644 "$DESKTOP_FILE" "$PKGROOT/usr/share/applications/$APP_NAME.desktop"

if [[ -f "$ICON_SOURCE_PNG" ]]; then
  install -m 0644 "$ICON_SOURCE_PNG" "$PKGROOT/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"
fi

if [[ -f "$ICON_SOURCE_SVG" ]]; then
  install -m 0644 "$ICON_SOURCE_SVG" "$PKGROOT/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg"
fi

"$FPM_BIN" -s dir -t rpm \
  -n "$APP_NAME" \
  -v "$VERSION" \
  --iteration "$ITERATION" \
  --architecture "$ARCH" \
  --description "KDE system tray app for Tailscale (requires tailscale CLI on PATH at runtime)" \
  --url "https://github.com/iamstevedavis/tailscale-tray" \
  --license "MIT" \
  --maintainer "Steve Davis" \
  -C "$PKGROOT" \
  .

echo "Built RPM(s):"
ls -1 "$ROOT_DIR"/*.rpm
