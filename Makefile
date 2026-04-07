APP_NAME := tailscale-tray
VERSION ?= 0.1.0
PYTHON ?= python3

.PHONY: test build-binary build-rpm clean

test:
	$(PYTHON) -m py_compile app.py tailscale_status.py
	$(PYTHON) -m unittest discover -s tests -v

build-binary: test
	./scripts/build-binary.sh

build-rpm: build-binary
	./scripts/build-rpm.sh $(VERSION)

clean:
	rm -rf build dist pkgroot *.spec.tmp
