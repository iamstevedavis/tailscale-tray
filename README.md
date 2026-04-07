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

## Packaging and installer

This repo includes a Fedora-friendly packaging flow:

- `./scripts/build-binary.sh` builds a self-contained PyInstaller binary
- `./scripts/build-rpm.sh <version>` wraps that binary in an RPM using `fpm`
- `make build-rpm VERSION=0.1.0` runs tests, builds the binary, then builds the RPM

### Fedora build dependencies

```bash
sudo dnf install -y python3 python3-pip rpm-build rpmdevtools desktop-file-utils
python3 -m pip install --user -r requirements-build.txt

sudo dnf install -y ruby ruby-devel gcc make
sudo gem install fpm
```

### Build RPM

```bash
make build-rpm VERSION=0.1.0
```

The resulting RPM can be installed with:

```bash
sudo dnf install ./tailscale-tray-0.1.0-1.$(uname -m).rpm
```

### Alternative spec file

A starter RPM spec is also included at:

```text
packaging/tailscale-tray.spec
```

That is useful if you later want to switch from `fpm` to `rpmbuild`/COPR style packaging.

## Desktop file

The desktop launcher used by the RPM lives at:

```text
packaging/tailscale-tray.desktop
```
