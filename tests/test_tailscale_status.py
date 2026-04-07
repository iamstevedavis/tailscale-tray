import os
import stat
import tempfile
import unittest

from tailscale_cli import detect_tailscale_path, missing_tailscale_message
from tailscale_status import ConnectionState, error_snapshot, parse_status_payload


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
        self.assertEqual(snapshot.summary, "NeedsLogin")

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


if __name__ == "__main__":
    unittest.main()
