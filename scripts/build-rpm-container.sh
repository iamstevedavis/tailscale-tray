#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="${1:-0.1.0}"
IMAGE_TAG="${IMAGE_TAG:-tailscale-tray-rpm-builder}"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-docker}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/artifacts}"
ARCH="${ARCH:-$(uname -m)}"
MOUNT_LABEL=""

if ! command -v "$CONTAINER_ENGINE" >/dev/null 2>&1; then
  echo "error: container engine not found: $CONTAINER_ENGINE" >&2
  exit 1
fi

if command -v getenforce >/dev/null 2>&1; then
  SELINUX_MODE="$(getenforce 2>/dev/null || true)"
  if [[ "$SELINUX_MODE" == "Enforcing" || "$SELINUX_MODE" == "Permissive" ]]; then
    MOUNT_LABEL=":Z"
  fi
fi

mkdir -p "$OUTPUT_DIR"

echo "Building container image: $IMAGE_TAG"
"$CONTAINER_ENGINE" build \
  -f packaging/Dockerfile.rpm-build \
  -t "$IMAGE_TAG" \
  .

echo "Building RPM in container"
"$CONTAINER_ENGINE" run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e VERSION="$VERSION" \
  -e ARCH="$ARCH" \
  -v "$ROOT_DIR":/src$MOUNT_LABEL \
  -v "$OUTPUT_DIR":/out$MOUNT_LABEL \
  -w /src \
  "$IMAGE_TAG" \
  bash -lc '
    set -euo pipefail
    rm -rf build dist pkgroot *.spec.tmp
    make build-rpm VERSION="$VERSION"
    cp -f ./*.rpm /out/
  '

echo "Artifacts written to: $OUTPUT_DIR"
ls -1 "$OUTPUT_DIR"/*.rpm
