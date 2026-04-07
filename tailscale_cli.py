import os
import shutil
from typing import Iterable


FALLBACK_TAILSCALE_PATHS = (
    "/var/lib/snapd/snap/bin/tailscale",
    "/snap/bin/tailscale",
    "/usr/local/bin/tailscale",
    "/usr/bin/tailscale",
)


def detect_tailscale_path(
    env_path: str | None = None,
    fallback_paths: Iterable[str] = FALLBACK_TAILSCALE_PATHS,
) -> str | None:
    path = shutil.which("tailscale", path=env_path) if env_path is not None else shutil.which("tailscale")
    if path:
        return path

    for candidate in fallback_paths:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None


def missing_tailscale_message() -> str:
    return (
        "Could not find the `tailscale` CLI. Install Tailscale or ensure the binary is on PATH. "
        "Snap installs are supported if their bin directory is available to desktop apps."
    )
