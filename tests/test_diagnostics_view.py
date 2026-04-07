import unittest

from diagnostics_view import build_diagnostics_view
from tailscale_status import ConnectionState, TailscaleSnapshot


class DiagnosticsViewTests(unittest.TestCase):
    def test_build_diagnostics_view_includes_snapshot_and_cli_details(self):
        snapshot = TailscaleSnapshot(
            state=ConnectionState.CONNECTED,
            backend_state="Running",
            tailnet_ip="100.64.0.1",
            tailnet_name="example.ts.net",
            device_name="fedora-laptop",
            exit_node="toronto-exit",
            error="",
        )

        view = build_diagnostics_view(snapshot, "/snap/bin/tailscale")

        self.assertEqual("Tailscale diagnostics", view.title)
        self.assertIn("State: Connected", view.message)
        self.assertIn("Backend: Running", view.message)
        self.assertIn("CLI path: /snap/bin/tailscale", view.message)
        self.assertIn("Tailnet IP: 100.64.0.1", view.message)
        self.assertIn("Tailnet: example.ts.net", view.message)
        self.assertIn("Device: fedora-laptop", view.message)
        self.assertIn("Exit node: toronto-exit", view.message)

    def test_build_diagnostics_view_handles_missing_values_cleanly(self):
        snapshot = TailscaleSnapshot(
            state=ConnectionState.ERROR,
            backend_state="status failed",
            tailnet_ip="",
            tailnet_name="",
            device_name="",
            exit_node="",
            error="tailscale not found",
        )

        view = build_diagnostics_view(snapshot, None)

        self.assertIn("CLI path: Not found", view.message)
        self.assertIn("Tailnet IP: Unavailable", view.message)
        self.assertIn("Tailnet: Unavailable", view.message)
        self.assertIn("Device: Unavailable", view.message)
        self.assertIn("Exit node: None", view.message)
        self.assertIn("Error: tailscale not found", view.message)


if __name__ == "__main__":
    unittest.main()
