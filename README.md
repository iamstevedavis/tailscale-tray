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

This repo includes two packaging flows:

- `make build-rpm VERSION=0.1.0`
  - builds directly on a Fedora host with local PyInstaller + `fpm`
- `make build-rpm-container VERSION=0.1.0`
  - builds inside a Fedora Docker container and writes the RPM back to the host under `./artifacts/`

### Recommended: containerized build

This avoids needing a Fedora workstation as the build host. You only need Docker.

```bash
make build-rpm-container VERSION=0.1.0
```

Or run the script directly:

```bash
./scripts/build-rpm-container.sh 0.1.0
```

On SELinux-enabled Fedora hosts, the script automatically applies the correct bind-mount relabeling for Docker.

That flow:

1. builds `packaging/Dockerfile.rpm-build`
2. installs PyInstaller and `fpm` inside the container
3. runs the normal build pipeline in the container
4. copies the generated RPM into `./artifacts/` on the host

Install the resulting artifact with:

```bash
sudo dnf install ./artifacts/tailscale-tray-0.1.0-1.$(uname -m).rpm
```

### Native Fedora build dependencies

If you still want to build natively on Fedora:

```bash
sudo dnf install -y python3 python3-pip rpm-build rpmdevtools desktop-file-utils
python3 -m pip install --user -r requirements-build.txt

sudo dnf install -y ruby ruby-devel gcc make
sudo gem install fpm
```

### Native build RPM

```bash
make build-rpm VERSION=0.1.0
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
