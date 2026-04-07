import os
import stat
import tempfile
import unittest

from tailscale_cli import detect_tailscale_path, missing_tailscale_message
from tailscale_command import analyze_tailscale_command
from tailscale_status import ConnectionState, TailscaleSnapshot, error_snapshot, parse_status_payload
from tray_view import build_tray_view


class TailscaleStatusTests(unittest.TestCase):
    def test_running_payload_is_connected(self):
        payload = {
            "BackendState": "Running",
            "CurrentTailnet": {"Name": "example.ts.net"},
            "Self": {
                "HostName": "fedora-laptop",
                "TailscaleIPs": ["100.64.0.1"],
                "ExitNodeStatus": "",
            },
        }

        snapshot = parse_status_payload(payload)

        self.assertEqual(snapshot.state, ConnectionState.CONNECTED)
        self.assertEqual(snapshot.tailnet_ip, "100.64.0.1")
        self.assertEqual(snapshot.tailnet_name, "example.ts.net")
        self.assertEqual(snapshot.device_name, "fedora-laptop")

    def test_needs_login_payload_maps_cleanly(self):
        payload = {"BackendState": "NeedsLogin", "Self": {}}

        snapshot = parse_status_payload(payload)

        self.assertEqual(snapshot.state, ConnectionState.NEEDS_LOGIN)
        self.assertEqual(snapshot.summary, "backend: NeedsLogin")

    def test_starting_payload_maps_to_connecting(self):
        payload = {"BackendState": "Starting", "Self": {"HostName": "fedora-laptop"}}

        snapshot = parse_status_payload(payload)

        self.assertEqual(snapshot.state, ConnectionState.CONNECTING)
        self.assertIn("backend: Starting", snapshot.summary)

    def test_machine_auth_payload_maps_to_needs_approval(self):
        payload = {"BackendState": "NeedsMachineAuth", "Self": {}}

        snapshot = parse_status_payload(payload)

        self.assertEqual(snapshot.state, ConnectionState.NEEDS_APPROVAL)

    def test_unknown_backend_state_is_not_treated_as_error(self):
        payload = {"BackendState": "WeirdFutureState", "Self": {}}

        snapshot = parse_status_payload(payload)

        self.assertEqual(snapshot.state, ConnectionState.UNKNOWN)
        self.assertEqual(snapshot.error, "")

    def test_error_snapshot_sets_error_state(self):
        snapshot = error_snapshot("command failed", "boom")

        self.assertEqual(snapshot.state, ConnectionState.ERROR)
        self.assertEqual(snapshot.error, "boom")

    def test_detect_tailscale_path_falls_back_to_known_locations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fallback = os.path.join(tmpdir, "tailscale")
            with open(fallback, "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\n")
            os.chmod(fallback, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

            detected = detect_tailscale_path(env_path="/definitely/missing", fallback_paths=(fallback,))

            self.assertEqual(detected, fallback)

    def test_missing_tailscale_message_mentions_snap(self):
        self.assertIn("Snap installs are supported", missing_tailscale_message())

    def test_command_feedback_detects_permission_problem(self):
        feedback = analyze_tailscale_command(
            "Connect",
            exit_code=1,
            stdout="",
            stderr="permission denied while talking to local tailscaled",
        )

        self.assertIn("permission", feedback.title.lower())

    def test_command_feedback_detects_tailscaled_not_running(self):
        feedback = analyze_tailscale_command(
            "Connect",
            exit_code=1,
            stdout="",
            stderr="failed to connect to local tailscaled; no such file or directory",
        )

        self.assertIn("tailscaled", feedback.title.lower())

    def test_command_feedback_detects_browser_login_requirement(self):
        feedback = analyze_tailscale_command(
            "Connect",
            exit_code=1,
            stdout="To authenticate, visit: https://login.tailscale.com/a/abc123",
            stderr="",
        )

        self.assertIn("browser login", feedback.title.lower())
        self.assertIn("https://login.tailscale.com/a/abc123", feedback.message)
        self.assertEqual("info", feedback.icon)

    def test_tray_view_enables_disconnect_for_connected_state(self):
        view = build_tray_view(
            TailscaleSnapshot(
                state=ConnectionState.CONNECTED,
                backend_state="Running",
                tailnet_ip="100.64.0.1",
                tailnet_name="example.ts.net",
                device_name="fedora-box",
                exit_node="",
            )
        )

        self.assertEqual("connected", view.icon)
        self.assertFalse(view.connect_enabled)
        self.assertTrue(view.disconnect_enabled)
        self.assertTrue(view.copy_ip_enabled)
        self.assertIn("example.ts.net", view.tooltip)

    def test_tray_view_enables_connect_for_needs_login_state(self):
        view = build_tray_view(
            TailscaleSnapshot(
                state=ConnectionState.NEEDS_LOGIN,
                backend_state="NeedsLogin",
                tailnet_ip="",
                tailnet_name="",
                device_name="",
                exit_node="",
            )
        )

        self.assertEqual("warning", view.icon)
        self.assertTrue(view.connect_enabled)
        self.assertFalse(view.disconnect_enabled)
        self.assertFalse(view.copy_ip_enabled)
        self.assertEqual("Status: Needs Login", view.status_text)

    def test_tray_view_shows_critical_missing_cli_state(self):
        snapshot = error_snapshot("tailscale not found", missing_tailscale_message())
        view = build_tray_view(snapshot)

        self.assertEqual("critical", view.icon)
        self.assertFalse(view.connect_enabled)
        self.assertFalse(view.disconnect_enabled)
        self.assertFalse(view.copy_ip_enabled)
        self.assertIn("tailscale not found", view.tooltip)
        self.assertIn("Snap installs are supported", view.tooltip)

    def test_command_feedback_detects_start_failure_as_critical(self):
        feedback = analyze_tailscale_command(
            "Connect",
            exit_code=None,
            stdout="",
            stderr="",
            process_error="execve failed",
        )

        self.assertEqual("critical", feedback.icon)
        self.assertIn("execve failed", feedback.message)


if __name__ == "__main__":
    unittest.main()
