APP_NAME := tailscale-tray
VERSION ?= 0.1.0
PYTHON ?= python3

.PHONY: test build-binary build-rpm build-rpm-container build-aur-artifact clean

test:
	$(PYTHON) -m py_compile \
		app.py \
		tailscale_status.py \
		tailscale_cli.py \
		tailscale_command.py \
		tray_view.py \
		tray_controller.py \
		diagnostics_view.py
	$(PYTHON) -m unittest discover -s tests -v

build-binary: test
	./scripts/build-binary.sh

build-rpm: build-binary
	./scripts/build-rpm.sh $(VERSION)

build-rpm-container:
	./scripts/build-rpm-container.sh $(VERSION)

build-aur-artifact:
	./scripts/build-aur-artifact.sh $(VERSION)

clean:
	rm -rf build dist pkgroot tailscale-tray.spec *.spec.tmp artifacts/PKGBUILD artifacts/.SRCINFO artifacts/*-arch-release.zip
