#!/usr/bin/env python3
import json
import sys
from typing import Optional

from PySide6.QtCore import QProcess, QTimer, QUrl
from PySide6.QtGui import QAction, QClipboard, QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QStyle, QSystemTrayIcon

from tailscale_cli import detect_tailscale_path, missing_tailscale_message
from tailscale_command import analyze_tailscale_command
from tailscale_status import ConnectionState, TailscaleSnapshot, error_snapshot, parse_status_payload
from tray_view import build_tray_view


MESSAGE_ICONS = {
    "info": QSystemTrayIcon.MessageIcon.Information,
    "warning": QSystemTrayIcon.MessageIcon.Warning,
    "critical": QSystemTrayIcon.MessageIcon.Critical,
}

TRAY_ICONS = {
    "connected": QStyle.StandardPixmap.SP_DialogApplyButton,
    "connecting": QStyle.StandardPixmap.SP_BrowserReload,
    "warning": QStyle.StandardPixmap.SP_MessageBoxWarning,
    "critical": QStyle.StandardPixmap.SP_MessageBoxCritical,
    "stopped": QStyle.StandardPixmap.SP_DialogCancelButton,
}

POLL_INTERVAL_MS = 10000
TAILSCALE_ADMIN_URL = "https://login.tailscale.com/admin/machines"


class TailscaleTray:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.tray = QSystemTrayIcon(self._icon_for_key("stopped"), app)
        self.tray.setToolTip("Tailscale Tray")
        self.menu = QMenu()
        self.tray.setContextMenu(self.menu)

        self.snapshot = TailscaleSnapshot(
            state=ConnectionState.STOPPED,
            backend_state="Unknown",
            tailnet_ip="",
            tailnet_name="",
            device_name="",
            exit_node="",
            error="",
        )
        self.command_process: Optional[QProcess] = None
        self.status_process: Optional[QProcess] = None
        self.pending_refresh = False
        self.tailscale_path = None

        self._build_menu()
        self._build_timer()
        self.refresh_status(initial=True)
        self.tray.show()

    def _build_menu(self) -> None:
        self.status_action = QAction("Status: checking…", self.menu)
        self.status_action.setEnabled(False)
        self.details_action = QAction("Details:", self.menu)
        self.details_action.setEnabled(False)

        self.refresh_action = QAction("Refresh", self.menu)
        self.refresh_action.triggered.connect(self.refresh_status)

        self.connect_action = QAction("Connect", self.menu)
        self.connect_action.triggered.connect(lambda: self.run_tailscale_command(["up"], "Connect"))

        self.disconnect_action = QAction("Disconnect", self.menu)
        self.disconnect_action.triggered.connect(lambda: self.run_tailscale_command(["down"], "Disconnect"))

        self.copy_ip_action = QAction("Copy Tailnet IP", self.menu)
        self.copy_ip_action.triggered.connect(self.copy_tailnet_ip)

        self.open_admin_action = QAction("Open Tailscale Admin", self.menu)
        self.open_admin_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl(TAILSCALE_ADMIN_URL))
        )

        self.quit_action = QAction("Quit", self.menu)
        self.quit_action.triggered.connect(self.app.quit)

        self.menu.addAction(self.status_action)
        self.menu.addAction(self.details_action)
        self.menu.addSeparator()
        self.menu.addAction(self.refresh_action)
        self.menu.addAction(self.connect_action)
        self.menu.addAction(self.disconnect_action)
        self.menu.addAction(self.copy_ip_action)
        self.menu.addAction(self.open_admin_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray.activated.connect(self._on_activated)

    def _build_timer(self) -> None:
        self.timer = QTimer(self.app)
        self.timer.setInterval(POLL_INTERVAL_MS)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.refresh_status()

    def _icon_for_key(self, icon_key: str) -> QIcon:
        return self.app.style().standardIcon(TRAY_ICONS[icon_key])

    def resolve_tailscale_path(self) -> str | None:
        self.tailscale_path = detect_tailscale_path()
        return self.tailscale_path

    def refresh_status(self, initial: bool = False) -> None:
        if self.status_process and self.status_process.state() != QProcess.ProcessState.NotRunning:
            self.pending_refresh = True
            return

        tailscale_path = self.resolve_tailscale_path()
        if not tailscale_path:
            self._apply_status_snapshot(
                error_snapshot("tailscale not found", missing_tailscale_message()),
                initial=initial,
            )
            return

        process = QProcess(self.app)
        process.setProgram(tailscale_path)
        process.setArguments(["status", "--json"])
        process.finished.connect(
            lambda code, status: self._status_finished(process, code, status, initial)
        )
        process.errorOccurred.connect(lambda _err: self._status_failed(process, initial))
        self.status_process = process
        process.start()

    def _apply_status_snapshot(self, snapshot: TailscaleSnapshot, initial: bool = False) -> None:
        previous_state = self.snapshot.state
        self.snapshot = snapshot
        self.apply_snapshot()

        if not initial and snapshot.state != previous_state:
            self.show_message("Tailscale status changed", f"{snapshot.state.value}: {snapshot.summary}")

    def _status_finished(
        self,
        process: QProcess,
        exit_code: int,
        _exit_status: QProcess.ExitStatus,
        initial: bool,
    ) -> None:
        stdout = bytes(process.readAllStandardOutput()).decode().strip()
        stderr = bytes(process.readAllStandardError()).decode().strip()

        if exit_code == 0:
            try:
                snapshot = parse_status_payload(json.loads(stdout))
            except json.JSONDecodeError as exc:
                snapshot = error_snapshot("invalid status output", str(exc))
        else:
            detail = stderr or stdout or f"status failed with exit code {exit_code}."
            snapshot = error_snapshot("command failed", detail)

        self._apply_status_snapshot(snapshot, initial=initial)
        self._finish_status_process(process)

    def _status_failed(self, process: QProcess, initial: bool) -> None:
        snapshot = error_snapshot("status failed", process.errorString() or "Failed to fetch Tailscale status.")
        self._apply_status_snapshot(snapshot, initial=initial)
        self._finish_status_process(process)

    def _finish_status_process(self, process: QProcess) -> None:
        process.deleteLater()
        if self.status_process is process:
            self.status_process = None

        if self.pending_refresh:
            self.pending_refresh = False
            self.refresh_status()

    def apply_snapshot(self) -> None:
        snapshot = self.snapshot
        view = build_tray_view(snapshot)
        self.tray.setIcon(self._icon_for_key(view.icon))
        self.status_action.setText(view.status_text)
        self.details_action.setText(view.details_text)
        self.tray.setToolTip(view.tooltip)
        self.copy_ip_action.setEnabled(view.copy_ip_enabled)
        self.connect_action.setEnabled(view.connect_enabled)
        self.disconnect_action.setEnabled(view.disconnect_enabled)

    def run_tailscale_command(self, args: list[str], action_name: str) -> None:
        tailscale_path = self.resolve_tailscale_path()
        if not tailscale_path:
            self.show_message("Tailscale missing", missing_tailscale_message(), QSystemTrayIcon.MessageIcon.Critical)
            return
        if self.command_process and self.command_process.state() != QProcess.ProcessState.NotRunning:
            self.show_message("Command already running", "Wait for the current Tailscale command to finish.")
            return

        process = QProcess(self.app)
        process.setProgram(tailscale_path)
        process.setArguments(args)
        process.started.connect(lambda: self._command_started(args, action_name))
        process.finished.connect(lambda code, status: self._command_finished(process, code, status, action_name))
        process.errorOccurred.connect(lambda _err: self._command_failed(process, action_name))
        self.command_process = process
        process.start()

    def _command_started(self, args: list[str], action_name: str) -> None:
        self.show_message(f"{action_name} started", f"Running: tailscale {' '.join(args)}")

    def _command_finished(self, process: QProcess, exit_code: int, _exit_status: QProcess.ExitStatus, action_name: str) -> None:
        stdout = bytes(process.readAllStandardOutput()).decode().strip()
        stderr = bytes(process.readAllStandardError()).decode().strip()
        feedback = analyze_tailscale_command(action_name, exit_code=exit_code, stdout=stdout, stderr=stderr)
        self.show_message(feedback.title, feedback.message, MESSAGE_ICONS[feedback.icon])
        self.refresh_status()
        process.deleteLater()
        self.command_process = None

    def _command_failed(self, process: QProcess, action_name: str) -> None:
        self.resolve_tailscale_path()
        feedback = analyze_tailscale_command(
            action_name,
            exit_code=None,
            stdout="",
            stderr="",
            process_error=process.errorString(),
        )
        self.show_message(feedback.title, feedback.message, MESSAGE_ICONS[feedback.icon])
        process.deleteLater()
        self.command_process = None
        self.refresh_status()

    def copy_tailnet_ip(self) -> None:
        if not self.snapshot.tailnet_ip:
            self.show_message("Copy Tailnet IP", "No tailnet IP available right now.")
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self.snapshot.tailnet_ip, mode=QClipboard.Mode.Clipboard)
        self.show_message("Copy Tailnet IP", f"Copied {self.snapshot.tailnet_ip}")

    def show_message(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
    ) -> None:
        self.tray.showMessage(title, message, icon, 4000)


def main() -> int:
    QApplication.setQuitOnLastWindowClosed(False)
    app = QApplication(sys.argv)
    app.setApplicationName("Tailscale Tray")

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Tailscale Tray", "No system tray is available in this session.")
        return 1

    tray = TailscaleTray(app)
    _ = tray
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
