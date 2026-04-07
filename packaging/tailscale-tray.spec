Name:           tailscale-tray
Version:        0.1.0
Release:        1%{?dist}
Summary:        KDE system tray helper for Tailscale
License:        MIT
URL:            https://github.com/iamstevedavis/tailscale-tray
BuildArch:      x86_64
# Runtime requirement: a working `tailscale` CLI must be available on PATH or a supported fallback path.

Source0:        dist/tailscale-tray
Source1:        packaging/tailscale-tray.desktop

%description
A small KDE-friendly system tray app for Fedora/Linux that wraps the tailscale CLI.
The app does not require the Fedora `tailscale` RPM specifically, but it does require a working `tailscale` binary at runtime.

%prep
# No source extraction needed for the prebuilt PyInstaller artifact.

%build
# Binary is built ahead of rpmbuild via PyInstaller.

%install
install -D -m 0755 %{SOURCE0} %{buildroot}%{_bindir}/tailscale-tray
install -D -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/tailscale-tray.desktop

%files
%{_bindir}/tailscale-tray
%{_datadir}/applications/tailscale-tray.desktop

%changelog
* Mon Apr 07 2026 Steve Davis <steve@example.com> - 0.1.0-1
- Initial RPM packaging for the PyInstaller-based tray app
