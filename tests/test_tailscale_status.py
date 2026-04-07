import unittest

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


if __name__ == "__main__":
    unittest.main()
