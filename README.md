# tailscale-tray

A small KDE-friendly system tray app for Fedora/Linux that wraps the `tailscale` CLI.

## MVP features

- Polls `tailscale status --json`
- Shows current state in the tray menu:
  - Connected
  - Disconnected
  - Needs Login
  - Error
- Quick actions:
  - Refresh
  - Connect
  - Disconnect
  - Copy Tailnet IP
  - Open Tailscale Admin
  - Quit
- Uses non-blocking command execution for `tailscale up` and `tailscale down`
- Shows tray notifications for status changes and action results

## Requirements

- Fedora KDE or another Linux desktop with StatusNotifier/system tray support
- Python 3.10+
- Tailscale CLI installed and working
- PySide6

## Install

### Fedora

```bash
sudo dnf install -y python3 python3-pip tailscale
python3 -m pip install --user -r requirements.txt
```

If Tailscale is not already authenticated:

```bash
sudo systemctl enable --now tailscaled
sudo tailscale up
```

## Run

```bash
python3 app.py
```

## Notes

- Some actions may require elevated privileges depending on how Tailscale is installed on your machine.
- The app intentionally stays simple. It shells out to the official `tailscale` CLI instead of reimplementing Tailscale behavior.
- The default admin link opens the machine list in the Tailscale admin console.

## Optional desktop launch

A sample desktop file is included at:

```text
packaging/tailscale-tray.desktop
```

You can copy it into:

```text
~/.local/share/applications/
```

and adjust the `Exec=` path for your checkout.
