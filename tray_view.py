from dataclasses import dataclass

from tailscale_status import ConnectionState, TailscaleSnapshot


@dataclass
class TrayViewState:
    icon: str
    status_text: str
    details_text: str
    tooltip: str
    copy_ip_enabled: bool
    connect_enabled: bool
    disconnect_enabled: bool


WARNING_STATES = {
    ConnectionState.NEEDS_LOGIN,
    ConnectionState.NEEDS_APPROVAL,
    ConnectionState.UNKNOWN,
}

CONNECTABLE_STATES = {
    ConnectionState.STOPPED,
    ConnectionState.NEEDS_LOGIN,
    ConnectionState.NEEDS_APPROVAL,
    ConnectionState.UNKNOWN,
}

DISCONNECTABLE_STATES = {
    ConnectionState.CONNECTED,
    ConnectionState.CONNECTING,
}


def build_tray_view(snapshot: TailscaleSnapshot) -> TrayViewState:
    return TrayViewState(
        icon=_icon_for_state(snapshot.state),
        status_text=f"Status: {snapshot.state.value}",
        details_text=f"Details: {snapshot.summary}",
        tooltip=_tooltip_for_snapshot(snapshot),
        copy_ip_enabled=bool(snapshot.tailnet_ip),
        connect_enabled=snapshot.state in CONNECTABLE_STATES,
        disconnect_enabled=snapshot.state in DISCONNECTABLE_STATES,
    )


def _icon_for_state(state: ConnectionState) -> str:
    if state == ConnectionState.CONNECTED:
        return "connected"
    if state == ConnectionState.CONNECTING:
        return "connecting"
    if state in WARNING_STATES:
        return "warning"
    if state == ConnectionState.ERROR:
        return "critical"
    return "stopped"


def _tooltip_for_snapshot(snapshot: TailscaleSnapshot) -> str:
    tooltip_lines = [
        f"Tailscale: {snapshot.state.value}",
        f"Backend: {snapshot.backend_state or 'Unknown'}",
    ]
    if snapshot.tailnet_name:
        tooltip_lines.append(snapshot.tailnet_name)
    if snapshot.tailnet_ip:
        tooltip_lines.append(snapshot.tailnet_ip)
    if snapshot.error:
        tooltip_lines.append(snapshot.error)
    return "\n".join(tooltip_lines)
