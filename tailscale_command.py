from dataclasses import dataclass


@dataclass
class CommandFeedback:
    title: str
    message: str
    icon: str


def analyze_tailscale_command(
    action_name: str,
    *,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    process_error: str = "",
) -> CommandFeedback:
    combined = "\n".join(part for part in (stderr, stdout, process_error) if part).strip()
    lower = combined.lower()

    if _is_permission_problem(lower):
        return CommandFeedback(
            title=f"{action_name} needs permission",
            message=(
                "Tailscale needs elevated permission or polkit approval on this system. "
                "Try running the command from a terminal or adjust local Tailscale permissions."
            ),
            icon="warning",
        )

    if _is_tailscaled_down(lower):
        return CommandFeedback(
            title="tailscaled is not running",
            message=(
                "The Tailscale daemon is unavailable. Start or restart tailscaled, then refresh the tray app."
            ),
            icon="warning",
        )

    login_url = _extract_auth_url(combined)
    if login_url:
        return CommandFeedback(
            title=f"{action_name} needs browser login",
            message=f"Finish Tailscale sign-in in your browser: {login_url}",
            icon="info",
        )

    if exit_code == 0:
        return CommandFeedback(
            title=action_name,
            message=stdout or f"{action_name} succeeded.",
            icon="info",
        )

    if process_error:
        return CommandFeedback(
            title=action_name,
            message=process_error or f"{action_name} failed to start.",
            icon="critical",
        )

    detail = combined or (
        f"{action_name} failed with exit code {exit_code}."
        if exit_code is not None
        else f"{action_name} failed to start."
    )
    return CommandFeedback(
        title=action_name,
        message=detail,
        icon="critical",
    )


def _is_permission_problem(lower: str) -> bool:
    needles = (
        "permission denied",
        "operation not permitted",
        "access denied",
        "polkit",
        "must be root",
        "not permitted",
    )
    return any(needle in lower for needle in needles)


def _is_tailscaled_down(lower: str) -> bool:
    needles = (
        "failed to connect to local tailscaled",
        "tailscaled.sock",
        "no such file or directory",
        "cannot connect to local tailscaled",
        "tailscaled is not running",
    )
    return any(needle in lower for needle in needles)


def _extract_auth_url(text: str) -> str | None:
    for token in text.replace("\n", " ").split():
        if token.startswith("https://") and "tailscale.com" in token:
            return token.rstrip(").,]")
    return None
