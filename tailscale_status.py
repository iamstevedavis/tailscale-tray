from dataclasses import dataclass
from enum import Enum


class ConnectionState(str, Enum):
    CONNECTED = "Connected"
    CONNECTING = "Connecting"
    STOPPED = "Stopped"
    NEEDS_LOGIN = "Needs Login"
    NEEDS_APPROVAL = "Needs Approval"
    UNKNOWN = "Unknown"
    ERROR = "Error"


@dataclass
class TailscaleSnapshot:
    state: ConnectionState
    backend_state: str
    tailnet_ip: str
    tailnet_name: str
    device_name: str
    exit_node: str
    error: str = ""

    @property
    def summary(self) -> str:
        details = []
        if self.device_name:
            details.append(self.device_name)
        if self.tailnet_ip:
            details.append(self.tailnet_ip)
        if self.exit_node:
            details.append(f"exit: {self.exit_node}")
        if self.backend_state:
            details.append(f"backend: {self.backend_state}")
        return " • ".join(details) or self.state.value


def error_snapshot(backend_state: str, message: str) -> TailscaleSnapshot:
    return TailscaleSnapshot(
        state=ConnectionState.ERROR,
        backend_state=backend_state,
        tailnet_ip="",
        tailnet_name="",
        device_name="",
        exit_node="",
        error=message,
    )


def parse_status_payload(payload: dict) -> TailscaleSnapshot:
    backend_state = payload.get("BackendState", "Unknown")
    self_info = payload.get("Self") or {}
    tailnet_ips = self_info.get("TailscaleIPs") or payload.get("TailscaleIPs") or []
    tailnet_ip = tailnet_ips[0] if tailnet_ips else ""
    tailnet_name = ((payload.get("CurrentTailnet") or {}).get("Name")) or ""
    device_name = self_info.get("HostName") or self_info.get("DNSName") or ""
    exit_node = self_info.get("ExitNodeStatus") or ""

    state_map = {
        "Running": ConnectionState.CONNECTED,
        "Starting": ConnectionState.CONNECTING,
        "Stopped": ConnectionState.STOPPED,
        "NeedsLogin": ConnectionState.NEEDS_LOGIN,
        "NeedsMachineAuth": ConnectionState.NEEDS_APPROVAL,
        "NoState": ConnectionState.STOPPED,
    }
    state = state_map.get(backend_state, ConnectionState.UNKNOWN)

    return TailscaleSnapshot(
        state=state,
        backend_state=backend_state,
        tailnet_ip=tailnet_ip,
        tailnet_name=tailnet_name,
        device_name=device_name,
        exit_node=exit_node,
        error="",
    )
