#!/usr/bin/env python3
import json
from dataclasses import dataclass
from typing import Callable, Protocol

from tailscale_command import analyze_tailscale_command
from tailscale_status import ConnectionState, TailscaleSnapshot, error_snapshot, parse_status_payload


class ProcessRunner(Protocol):
    def start(
        self,
        program: str,
        args: list[str],
        *,
        on_started: Callable[[], None] | None = None,
        on_finished: Callable[[int, str, str], None],
        on_error: Callable[[str], None],
    ) -> object: ...

    def is_running(self, handle: object) -> bool: ...

    def delete(self, handle: object) -> None: ...


@dataclass
class TrayMessage:
    title: str
    message: str
    icon: str = "info"


class TrayController:
    def __init__(
        self,
        *,
        runner: ProcessRunner,
        resolve_tailscale_path: Callable[[], str | None],
        missing_tailscale_message: Callable[[], str],
        on_snapshot: Callable[[TailscaleSnapshot, bool], None],
        on_message: Callable[[TrayMessage], None],
    ) -> None:
        self.runner = runner
        self.resolve_tailscale_path = resolve_tailscale_path
        self.missing_tailscale_message = missing_tailscale_message
        self.on_snapshot = on_snapshot
        self.on_message = on_message

        self.snapshot = TailscaleSnapshot(
            state=ConnectionState.STOPPED,
            backend_state="Unknown",
            tailnet_ip="",
            tailnet_name="",
            device_name="",
            exit_node="",
            error="",
        )
        self.status_handle: object | None = None
        self.command_handle: object | None = None
        self.pending_refresh = False

    def refresh_status(self, initial: bool = False) -> None:
        if self.status_handle and self.runner.is_running(self.status_handle):
            self.pending_refresh = True
            return

        tailscale_path = self.resolve_tailscale_path()
        if not tailscale_path:
            self._apply_status_snapshot(
                error_snapshot("tailscale not found", self.missing_tailscale_message()),
                initial=initial,
            )
            return

        handle_box: dict[str, object] = {}
        handle_box["handle"] = self.runner.start(
            tailscale_path,
            ["status", "--json"],
            on_finished=lambda exit_code, stdout, stderr: self._status_finished(
                handle_box["handle"], exit_code, stdout, stderr, initial
            ),
            on_error=lambda error_text: self._status_failed(handle_box["handle"], error_text, initial),
        )
        self.status_handle = handle_box["handle"]

    def run_tailscale_command(self, args: list[str], action_name: str) -> None:
        tailscale_path = self.resolve_tailscale_path()
        if not tailscale_path:
            self.on_message(TrayMessage("Tailscale missing", self.missing_tailscale_message(), "critical"))
            return

        if self.command_handle and self.runner.is_running(self.command_handle):
            self.on_message(TrayMessage("Command already running", "Wait for the current Tailscale command to finish."))
            return

        handle_box: dict[str, object] = {}
        handle_box["handle"] = self.runner.start(
            tailscale_path,
            args,
            on_started=lambda: self._command_started(args, action_name),
            on_finished=lambda exit_code, stdout, stderr: self._command_finished(
                handle_box["handle"], exit_code, stdout, stderr, action_name
            ),
            on_error=lambda error_text: self._command_failed(handle_box["handle"], error_text, action_name),
        )
        self.command_handle = handle_box["handle"]

    def _apply_status_snapshot(self, snapshot: TailscaleSnapshot, initial: bool = False) -> None:
        previous_state = self.snapshot.state
        self.snapshot = snapshot
        self.on_snapshot(snapshot, initial)

        if not initial and snapshot.state != previous_state:
            self.on_message(
                TrayMessage("Tailscale status changed", f"{snapshot.state.value}: {snapshot.summary}")
            )

    def _status_finished(
        self,
        handle: object,
        exit_code: int,
        stdout: str,
        stderr: str,
        initial: bool,
    ) -> None:
        if exit_code == 0:
            try:
                snapshot = parse_status_payload(json.loads(stdout))
            except json.JSONDecodeError as exc:
                snapshot = error_snapshot("invalid status output", str(exc))
        else:
            detail = stderr or stdout or f"status failed with exit code {exit_code}."
            snapshot = error_snapshot("command failed", detail)

        self._apply_status_snapshot(snapshot, initial=initial)
        self._finish_status_process(handle)

    def _status_failed(self, handle: object, error_text: str, initial: bool) -> None:
        snapshot = error_snapshot("status failed", error_text or "Failed to fetch Tailscale status.")
        self._apply_status_snapshot(snapshot, initial=initial)
        self._finish_status_process(handle)

    def _finish_status_process(self, handle: object) -> None:
        self.runner.delete(handle)
        if self.status_handle is handle:
            self.status_handle = None

        if self.pending_refresh:
            self.pending_refresh = False
            self.refresh_status()

    def _command_started(self, args: list[str], action_name: str) -> None:
        self.on_message(TrayMessage(f"{action_name} started", f"Running: tailscale {' '.join(args)}"))

    def _command_finished(
        self,
        handle: object,
        exit_code: int,
        stdout: str,
        stderr: str,
        action_name: str,
    ) -> None:
        feedback = analyze_tailscale_command(action_name, exit_code=exit_code, stdout=stdout, stderr=stderr)
        self.on_message(TrayMessage(feedback.title, feedback.message, feedback.icon))
        self.runner.delete(handle)
        self.command_handle = None
        self.refresh_status()

    def _command_failed(self, handle: object, error_text: str, action_name: str) -> None:
        self.resolve_tailscale_path()
        feedback = analyze_tailscale_command(
            action_name,
            exit_code=None,
            stdout="",
            stderr="",
            process_error=error_text,
        )
        self.on_message(TrayMessage(feedback.title, feedback.message, feedback.icon))
        self.runner.delete(handle)
        self.command_handle = None
        self.refresh_status()
