#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="${1:-0.1.0}"
IMAGE_TAG="${IMAGE_TAG:-tailscale-tray-rpm-builder}"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-docker}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/artifacts}"
ARCH="${ARCH:-$(uname -m)}"

if ! command -v "$CONTAINER_ENGINE" >/dev/null 2>&1; then
  echo "error: container engine not found: $CONTAINER_ENGINE" >&2
  exit 1
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
  -e VERSION="$VERSION" \
  -e ARCH="$ARCH" \
  -v "$ROOT_DIR":/src \
  -v "$OUTPUT_DIR":/out \
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
