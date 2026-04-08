# Release checklist

Use this when cutting a new `tailscale-tray` release.

## Before tagging

- [ ] `make test` passes locally
- [ ] README matches current behavior and packaging flow
- [ ] release workflow files still match the documented versioning approach
- [ ] desktop file, spec file, and packaging scripts are in sync
- [ ] visible UI changes have screenshots or notes for release context
- [ ] there are no accidental debug prints or temporary workarounds left in the app

## Choose a version

Use semver-style tags:

- patch: `v0.1.1` for fixes and small polish
- minor: `v0.2.0` for visible features or workflow improvements
- major: `v1.0.0` for breaking or milestone releases

## Create the release

```bash
git tag v0.1.1
git push origin v0.1.1
```

This triggers the GitHub Actions release workflow, which:
- runs the build in Docker
- produces the RPM
- uploads workflow artifacts
- creates a GitHub Release
- attaches the RPM and `SHA256SUMS.txt`

## Manual release option

If needed, use the GitHub Actions **Release RPM** workflow manually and provide:
- `0.1.1` or `v0.1.1`
- prerelease flag if appropriate

## After release

- [ ] confirm the GitHub Release exists
- [ ] confirm the RPM downloads correctly
- [ ] confirm `SHA256SUMS.txt` is attached
- [ ] spot-check install instructions from README against the released artifact name
- [ ] if this is a notable UX change, add screenshots to the README or release notes

## Nice-to-have follow-up

- [ ] note known issues in release notes if there are desktop-environment-specific quirks
- [ ] open follow-up issues for deferred cleanup rather than hiding them in memory
