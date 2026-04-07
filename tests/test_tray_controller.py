import unittest

from tray_controller import TrayController, TrayMessage
from tailscale_status import ConnectionState


class FakeHandle:
    def __init__(self, program, args, on_started, on_finished, on_error):
        self.program = program
        self.args = args
        self.on_started = on_started
        self.on_finished = on_finished
        self.on_error = on_error
        self.running = True
        self.deleted = False


class FakeRunner:
    def __init__(self):
        self.handles = []

    def start(self, program, args, *, on_started=None, on_finished, on_error):
        handle = FakeHandle(program, args, on_started, on_finished, on_error)
        self.handles.append(handle)
        return handle

    def is_running(self, handle):
        return handle.running

    def delete(self, handle):
        handle.deleted = True

    def emit_started(self, handle):
        if handle.on_started is not None:
            handle.on_started()

    def emit_finished(self, handle, exit_code=0, stdout="", stderr=""):
        handle.running = False
        handle.on_finished(exit_code, stdout, stderr)

    def emit_error(self, handle, error_text="boom"):
        handle.running = False
        handle.on_error(error_text)


class TrayControllerTests(unittest.TestCase):
    def make_controller(self, resolver=lambda: "/usr/bin/tailscale"):
        self.snapshots = []
        self.messages = []
        self.runner = FakeRunner()
        return TrayController(
            runner=self.runner,
            resolve_tailscale_path=resolver,
            missing_tailscale_message=lambda: "tailscale missing",
            on_snapshot=lambda snapshot, initial: self.snapshots.append((snapshot, initial)),
            on_message=lambda message: self.messages.append(message),
        )

    def test_refresh_status_coalesces_while_process_running(self):
        controller = self.make_controller()

        controller.refresh_status(initial=True)
        first = self.runner.handles[0]
        controller.refresh_status()

        self.assertTrue(controller.pending_refresh)
        self.assertEqual(1, len(self.runner.handles))

        self.runner.emit_finished(first, stdout='{"BackendState":"Running","Self":{}}')

        self.assertFalse(controller.pending_refresh)
        self.assertEqual(2, len(self.runner.handles))
        self.assertTrue(first.deleted)

    def test_run_command_only_shows_started_after_process_started(self):
        controller = self.make_controller()

        controller.run_tailscale_command(["up"], "Connect")
        handle = self.runner.handles[0]

        self.assertEqual([], self.messages)
        self.runner.emit_started(handle)
        self.assertEqual("Connect started", self.messages[0].title)

    def test_run_command_missing_cli_reports_critical(self):
        controller = self.make_controller(resolver=lambda: None)

        controller.run_tailscale_command(["up"], "Connect")

        self.assertEqual(0, len(self.runner.handles))
        self.assertEqual("Tailscale missing", self.messages[0].title)
        self.assertEqual("critical", self.messages[0].icon)

    def test_command_error_refreshes_status_after_failure(self):
        controller = self.make_controller()

        controller.run_tailscale_command(["up"], "Connect")
        command_handle = self.runner.handles[0]
        self.runner.emit_error(command_handle, "permission denied")

        self.assertTrue(command_handle.deleted)
        self.assertIsNone(controller.command_handle)
        self.assertEqual(2, len(self.runner.handles))
        self.assertEqual(["status", "--json"], self.runner.handles[1].args)
        self.assertEqual("Connect needs permission", self.messages[0].title)

    def test_status_change_emits_notification_outside_initial_refresh(self):
        controller = self.make_controller()

        controller.refresh_status(initial=True)
        first = self.runner.handles[0]
        self.runner.emit_finished(first, stdout='{"BackendState":"Stopped","Self":{}}')
        self.messages.clear()

        controller.refresh_status()
        second = self.runner.handles[1]
        self.runner.emit_finished(second, stdout='{"BackendState":"Running","Self":{}}')

        self.assertEqual(ConnectionState.CONNECTED, controller.snapshot.state)
        self.assertTrue(any(isinstance(message, TrayMessage) and message.title == "Tailscale status changed" for message in self.messages))


if __name__ == "__main__":
    unittest.main()
