# Contributing

Thanks for helping improve `tailscale-tray`.

## Scope and goals

This project is intentionally small.

Please prefer:
- focused fixes
- small, reviewable pull requests
- targeted UX improvements
- tests for behavior changes when practical

Please avoid unrelated refactors or dependency churn unless there is a clear reason.

## Development setup

### Run tests

```bash
make test
```

### Run from source

```bash
python3 -m pip install --user -r requirements.txt
python3 app.py
```

### Build an RPM in Docker

```bash
make build-rpm-container VERSION=0.1.0
```

## Repo structure

- `app.py` - Qt wiring and tray app entrypoint
- `tray_controller.py` - controller/process lifecycle logic
- `tray_view.py` - pure presentation rules for tray state
- `diagnostics_view.py` - pure diagnostics presenter
- `tailscale_status.py` - parses `tailscale status --json`
- `tailscale_command.py` - interprets command outcomes/failures
- `tailscale_cli.py` - CLI path detection helpers
- `tray_icon.py` - branded icon rendering
- `tests/` - unit tests
- `packaging/` - desktop entry, spec file, Docker builder
- `scripts/` - build helpers

## Contribution guidelines

- Keep changes narrow and purposeful
- Add or update tests when behavior changes
- Preserve headless testability for pure logic where possible
- Prefer pure helpers/presenters/controllers over pushing more logic into Qt widgets
- Keep Linux/KDE-first assumptions explicit in docs
- Do not add a hard runtime dependency on a specific Tailscale package if a working CLI is enough

## Pull requests

Before opening a PR:
- run `make test`
- update README/docs if behavior changed
- mention packaging or desktop-environment assumptions
- include screenshots if the UI changed visibly

Good PRs usually include:
- what changed
- why it changed
- how it was tested
- any limitations or follow-up ideas

## Release/versioning notes

Releases are tag-driven.

Examples:

```bash
git tag v0.1.1
git push origin v0.1.1
```

That triggers the GitHub release workflow and publishes the RPM artifact.

For maintainers, see `RELEASE_CHECKLIST.md`.
