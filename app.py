#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

from PySide6.QtCore import QProcess, QTimer, QUrl
from PySide6.QtGui import QAction, QClipboard, QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from diagnostics_view import build_diagnostics_view
from tailscale_cli import detect_tailscale_path, missing_tailscale_message
from tailscale_status import ConnectionState, TailscaleSnapshot
from tray_controller import TrayController, TrayMessage
from tray_icon import build_tray_icon
from tray_view import build_tray_view


MESSAGE_ICONS = {
    "info": QSystemTrayIcon.MessageIcon.Information,
    "warning": QSystemTrayIcon.MessageIcon.Warning,
    "critical": QSystemTrayIcon.MessageIcon.Critical,
}

POLL_INTERVAL_MS = 10000
TAILSCALE_ADMIN_URL = "https://login.tailscale.com/admin/machines"


class QtProcessRunner:
    def __init__(self, parent: QApplication) -> None:
        self.parent = parent

    def start(self, program, args, *, on_started=None, on_finished, on_error):
        process = QProcess(self.parent)
        process.setProgram(program)
        process.setArguments(args)
        if on_started is not None:
            process.started.connect(on_started)
        process.finished.connect(
            lambda code, _status: on_finished(
                code,
                bytes(process.readAllStandardOutput()).decode().strip(),
                bytes(process.readAllStandardError()).decode().strip(),
            )
        )
        process.errorOccurred.connect(lambda _err: on_error(process.errorString() or "Process failed."))
        process.start()
        return process

    def is_running(self, handle) -> bool:
        return handle.state() != QProcess.ProcessState.NotRunning

    def delete(self, handle) -> None:
        handle.deleteLater()


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
        self.controller = TrayController(
            runner=QtProcessRunner(app),
            resolve_tailscale_path=self.resolve_tailscale_path,
            missing_tailscale_message=missing_tailscale_message,
            on_snapshot=self._apply_controller_snapshot,
            on_message=self._show_controller_message,
        )
        self.tailscale_path = None

        self._build_menu()
        self._build_timer()
        self.controller.refresh_status(initial=True)
        self.tray.show()

    def _build_menu(self) -> None:
        self.status_action = QAction("Status: checking…", self.menu)
        self.status_action.setEnabled(False)
        self.details_action = QAction("Details:", self.menu)
        self.details_action.setEnabled(False)

        self.refresh_action = QAction("Refresh", self.menu)
        self.refresh_action.triggered.connect(self.controller.refresh_status)

        self.connect_action = QAction("Connect", self.menu)
        self.connect_action.triggered.connect(lambda: self.controller.run_tailscale_command(["up"], "Connect"))

        self.disconnect_action = QAction("Disconnect", self.menu)
        self.disconnect_action.triggered.connect(lambda: self.controller.run_tailscale_command(["down"], "Disconnect"))

        self.copy_ip_action = QAction("Copy Tailnet IP", self.menu)
        self.copy_ip_action.triggered.connect(self.copy_tailnet_ip)

        self.open_admin_action = QAction("Open Tailscale Admin", self.menu)
        self.open_admin_action.triggered.connect(self.open_tailscale_admin)

        self.show_diagnostics_action = QAction("Show diagnostics", self.menu)
        self.show_diagnostics_action.triggered.connect(self.show_diagnostics)

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
        self.menu.addAction(self.show_diagnostics_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray.activated.connect(self._on_activated)

    def _build_timer(self) -> None:
        self.timer = QTimer(self.app)
        self.timer.setInterval(POLL_INTERVAL_MS)
        self.timer.timeout.connect(self.controller.refresh_status)
        self.timer.start()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.controller.refresh_status()

    def _icon_for_key(self, icon_key: str) -> QIcon:
        return build_tray_icon(icon_key)

    def resolve_tailscale_path(self) -> str | None:
        self.tailscale_path = detect_tailscale_path()
        return self.tailscale_path

    def _apply_controller_snapshot(self, snapshot: TailscaleSnapshot, _initial: bool) -> None:
        self.snapshot = snapshot
        self.apply_snapshot()

    def _show_controller_message(self, message: TrayMessage) -> None:
        self.show_message(message.title, message.message, MESSAGE_ICONS[message.icon])

    def apply_snapshot(self) -> None:
        view = build_tray_view(self.snapshot)
        self.tray.setIcon(self._icon_for_key(view.icon))
        self.status_action.setText(view.status_text)
        self.details_action.setText(view.details_text)
        self.tray.setToolTip(view.tooltip)
        self.copy_ip_action.setEnabled(view.copy_ip_enabled)
        self.connect_action.setEnabled(view.connect_enabled)
        self.disconnect_action.setEnabled(view.disconnect_enabled)

    def copy_tailnet_ip(self) -> None:
        if not self.snapshot.tailnet_ip:
            self.show_message("Copy Tailnet IP", "No tailnet IP available right now.")
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self.snapshot.tailnet_ip, mode=QClipboard.Mode.Clipboard)
        self.show_message("Copy Tailnet IP", f"Copied {self.snapshot.tailnet_ip}")

    def show_diagnostics(self) -> None:
        diagnostics = build_diagnostics_view(self.snapshot, self.resolve_tailscale_path())
        QMessageBox.information(None, diagnostics.title, diagnostics.message)

    def open_tailscale_admin(self) -> None:
        xdg_open = shutil.which("xdg-open")
        if xdg_open:
            clean_env = os.environ.copy()
            for key in (
                "LD_LIBRARY_PATH",
                "QT_PLUGIN_PATH",
                "QML2_IMPORT_PATH",
                "PYINSTALLER_SUPPRESS_SPLASH_SCREEN",
                "PYINSTALLER_RESET_ENVIRONMENT",
                "PYTHONHOME",
                "PYTHONPATH",
            ):
                clean_env.pop(key, None)
            try:
                subprocess.Popen(
                    [xdg_open, TAILSCALE_ADMIN_URL],
                    env=clean_env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
            except OSError:
                pass

        ok = QDesktopServices.openUrl(QUrl(TAILSCALE_ADMIN_URL))
        if ok:
            return

        message = "Could not open the Tailscale Admin page. Check your default browser or URL handler."
        self.show_message(
            "Open Tailscale Admin",
            message,
            QSystemTrayIcon.MessageIcon.Warning,
        )
        QMessageBox.warning(None, "Open Tailscale Admin", message)

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
    app.setWindowIcon(build_tray_icon("connected"))

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Tailscale Tray", "No system tray is available in this session.")
        return 1

    tray = TailscaleTray(app)
    _ = tray
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
