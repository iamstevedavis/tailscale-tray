#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

SOURCE_URL="https://github.com/iamstevedavis/tailscale-tray/archive/refs/tags/v${VERSION}.tar.gz"
SOURCE_TARBALL="${WORK_DIR}/tailscale-tray-${VERSION}.tar.gz"
PKGBUILD_PATH="${ARTIFACTS_DIR}/PKGBUILD"
SRCINFO_PATH="${ARTIFACTS_DIR}/.SRCINFO"
AUR_BUNDLE_PATH="${ARTIFACTS_DIR}/tailscale-tray-${VERSION}-aur.tar.gz"

mkdir -p "${ARTIFACTS_DIR}"

curl -fsSL "${SOURCE_URL}" -o "${SOURCE_TARBALL}"
SOURCE_SHA256="$(sha256sum "${SOURCE_TARBALL}" | awk '{print $1}')"

sed \
  -e "s/@VERSION@/${VERSION}/g" \
  -e "s/@SHA256@/${SOURCE_SHA256}/g" \
  "${ROOT_DIR}/packaging/arch/PKGBUILD.in" > "${PKGBUILD_PATH}"

if command -v makepkg >/dev/null 2>&1; then
  (
    cd "${ARTIFACTS_DIR}"
    makepkg --printsrcinfo > ".SRCINFO"
  )
else
  docker run --rm \
    --user "$(id -u):$(id -g)" \
    -v "${ARTIFACTS_DIR}:/work" \
    -w /work \
    archlinux:base-devel \
    bash -lc 'makepkg --printsrcinfo > .SRCINFO'
fi

rm -f "${AUR_BUNDLE_PATH}"
tar -C "${ARTIFACTS_DIR}" -czf "${AUR_BUNDLE_PATH}" PKGBUILD .SRCINFO

echo "Built AUR artifacts:"
echo "  ${PKGBUILD_PATH}"
echo "  ${SRCINFO_PATH}"
echo "  ${AUR_BUNDLE_PATH}"
