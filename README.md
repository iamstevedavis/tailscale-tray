# tailscale-tray

[![CI](https://github.com/iamstevedavis/tailscale-tray/actions/workflows/ci.yml/badge.svg)](https://github.com/iamstevedavis/tailscale-tray/actions/workflows/ci.yml)
[![Release RPM](https://github.com/iamstevedavis/tailscale-tray/actions/workflows/release.yml/badge.svg)](https://github.com/iamstevedavis/tailscale-tray/actions/workflows/release.yml)
[![Latest Release](https://img.shields.io/github/v/release/iamstevedavis/tailscale-tray)](https://github.com/iamstevedavis/tailscale-tray/releases/latest)

A small KDE-friendly Linux system tray app for Tailscale.

It wraps the official `tailscale` CLI, shows current connection state in the tray, and gives quick desktop actions for common tasks without trying to replace the Tailscale client itself.

## Who this is for

- KDE Plasma users who want a lightweight tray app
- Fedora users first, other Linux desktops second
- People who already have a working Tailscale CLI install and want a friendlier desktop control surface

## Preview

Current packaged app icon:

<p align="center">
  <img src="assets/tailscale-tray.svg" alt="tailscale-tray icon" width="128" />
</p>

A fuller screenshots section is still on the roadmap. For now, the icon and README cover the current UX shape, and real KDE screenshots can be added as the UI settles.

## Features

- Branded TS tray icon with per-state status overlays
- Polls `tailscale status --json`
- Shows current state in the tray menu:
  - Connected
  - Connecting
  - Stopped
  - Needs Login
  - Needs Approval
  - Unknown
  - Error
- Quick actions:
  - Refresh
  - Connect
  - Disconnect
  - Copy Tailnet IP
  - Open Tailscale Admin
  - Show diagnostics
  - Quit
- Non-blocking status refresh and command execution
- Tray notifications for important state changes and action results
- Diagnostics view for backend state, CLI path, tailnet identity, and current error details
- Snap-friendly CLI detection, plus common fallback binary paths

## Requirements

- Linux desktop with StatusNotifier/system tray support
- KDE Plasma is the primary target and tested path
- Python 3.10+
- A working `tailscale` CLI installation
- PySide6

## Install

### RPM install

Download the latest RPM from GitHub Releases, then install it:

```bash
sudo dnf install ./tailscale-tray-<version>-1.$(uname -m).rpm
```

To reinstall the same version during testing:

```bash
sudo dnf reinstall ./tailscale-tray-<version>-1.$(uname -m).rpm
```

To uninstall:

```bash
sudo dnf remove tailscale-tray
```

### Runtime dependency

This app does not require the Fedora `tailscale` RPM specifically. It only needs a working `tailscale` CLI available at runtime.

Lookup order is:
- normal `PATH`
- `/var/lib/snapd/snap/bin/tailscale`
- `/snap/bin/tailscale`
- `/usr/local/bin/tailscale`
- `/usr/bin/tailscale`

That means Snap installs are supported as long as the desktop session can access the binary.

### If Tailscale is not authenticated yet

```bash
sudo systemctl enable --now tailscaled
sudo tailscale up
```

## Usage

Launch from your app launcher as **Tailscale Tray**, or run:

```bash
tailscale-tray
```

Menu actions:
- **Refresh**: re-checks current Tailscale state
- **Connect**: runs `tailscale up`
- **Disconnect**: runs `tailscale down`
- **Copy Tailnet IP**: copies the currently detected tailnet IP
- **Open Tailscale Admin**: opens the machine list in the Tailscale admin console
- **Show diagnostics**: shows current state, backend state, detected CLI path, tailnet info, and current error

## Troubleshooting

### Tray icon does not appear

- Confirm your desktop supports StatusNotifier/system tray icons
- On KDE, try logging out and back in if the tray host is misbehaving
- Start it from a terminal once to catch runtime errors:

```bash
tailscale-tray
```

### Tailscale CLI is not detected

Make sure one of these works from the same user session that launches the app:

```bash
which tailscale
ls -l /var/lib/snapd/snap/bin/tailscale /snap/bin/tailscale /usr/local/bin/tailscale /usr/bin/tailscale
```

If the binary exists but the app still cannot find it, open **Show diagnostics** and check the detected CLI path.

### Open Tailscale Admin does nothing

The app tries a sanitized `xdg-open` launch first, then falls back to Qt URL opening. If it still fails:

```bash
xdg-open https://login.tailscale.com/admin/machines
```

If that shell command works but the app action does not, file an issue with your desktop environment, distro, install method, and whether the packaged app was installed from the RPM.

### Connect or Disconnect fails

Some systems need polkit auth, elevated privileges, or an already-running `tailscaled` daemon. Use **Show diagnostics** and the tray notification text to see whether the failure looks like:
- permission/polkit
- `tailscaled` not running
- browser login required
- generic command failure

## Development

### Test locally

```bash
make test
```

### Run from source

```bash
python3 -m pip install --user -r requirements.txt
python3 app.py
```

## Packaging

This repo supports two RPM build flows.

### Recommended: containerized build

This is the easiest and most reproducible option. It only requires Docker on the host.

```bash
make build-rpm-container VERSION=0.1.0
```

Or directly:

```bash
./scripts/build-rpm-container.sh 0.1.0
```

That flow:
- builds `packaging/Dockerfile.rpm-build`
- runs the PyInstaller + RPM build inside a Fedora container
- writes finished artifacts to `./artifacts/`

On SELinux-enabled Fedora hosts, the script automatically applies the correct Docker bind-mount relabeling.

### Native Fedora build

If you want to build on a Fedora host directly:

```bash
sudo dnf install -y python3 python3-pip rpm-build rpmdevtools desktop-file-utils
python3 -m pip install --user -r requirements-build.txt
sudo dnf install -y ruby ruby-devel gcc make
sudo gem install fpm
make build-rpm VERSION=0.1.0
```

### Desktop file and spec

Key packaging files:
- `packaging/tailscale-tray.desktop`
- `packaging/tailscale-tray.spec`
- `packaging/Dockerfile.rpm-build`

## CI and releases

GitHub Actions now handles both validation and release packaging.

### CI

On pushes to `master` and on pull requests:
- runs `make test`

### Releases

There is a release workflow that:
- builds the RPM in Docker
- uploads workflow artifacts
- creates a GitHub Release
- attaches the built RPM and `SHA256SUMS.txt`
- uses tag-driven versioning
- generates release notes automatically
- respects `.github/release.yml` changelog categories

Release versioning is based on Git tags like:

```bash
v0.1.0
v0.1.1
v0.2.0
```

You can trigger releases in two ways:
- push a tag like `v0.1.1`
- run the **Release RPM** workflow manually and provide `0.1.1` or `v0.1.1`

## Roadmap / known limitations

- KDE-first, Linux-only for now
- No DE-specific packaging beyond RPM yet
- No auto-update mechanism yet
- No autostart installer flow yet

## Contributing

Issues and PRs are welcome.

See:
- `CONTRIBUTING.md`
- `RELEASE_CHECKLIST.md`
- `.github/ISSUE_TEMPLATE/`

Useful commands:

```bash
make test
make build-rpm-container VERSION=0.1.0
```

## Maintainer notes

If you are shipping a release:
- use `RELEASE_CHECKLIST.md`
- prefer tagging `vX.Y.Z`
- let GitHub Actions build and attach the RPM instead of hand-uploading artifacts
