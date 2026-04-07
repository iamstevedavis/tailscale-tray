from dataclasses import dataclass

from tailscale_status import TailscaleSnapshot


@dataclass
class DiagnosticsView:
    title: str
    message: str


def build_diagnostics_view(snapshot: TailscaleSnapshot, tailscale_path: str | None) -> DiagnosticsView:
    lines = [
        f"State: {snapshot.state.value}",
        f"Backend: {snapshot.backend_state or 'Unknown'}",
        f"CLI path: {tailscale_path or 'Not found'}",
        f"Tailnet IP: {snapshot.tailnet_ip or 'Unavailable'}",
        f"Tailnet: {snapshot.tailnet_name or 'Unavailable'}",
        f"Device: {snapshot.device_name or 'Unavailable'}",
        f"Exit node: {snapshot.exit_node or 'None'}",
    ]
    if snapshot.error:
        lines.append(f"Error: {snapshot.error}")

    return DiagnosticsView(
        title="Tailscale diagnostics",
        message="\n".join(lines),
    )
