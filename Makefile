ifeq ($(OS),Windows_NT)
PYTHON ?= ./.venv/Scripts/python.exe
UV ?= py -3 -m uv
BOOTSTRAP_PYTHON ?= py -3
else
PYTHON ?= ./.venv/bin/python
UV ?= uv
BOOTSTRAP_PYTHON ?= python3
endif

.PHONY: init sync uv-init uv-update uv-reset uv-ci package treemap lint fmt test test-cloud clean ai-refresh restore

init:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py init

uv-init:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py init

sync: uv-init

uv-update:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py update

uv-reset:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py reset

uv-ci:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py ci

package:
	$(PYTHON) scripts/package.py

treemap:
	$(PYTHON) scripts/generate_treemap.py

lint:
	$(PYTHON) scripts/testing/run_ruff_check.py

fmt:
	$(PYTHON) scripts/testing/run_ruff_format.py

test:
	$(PYTHON) scripts/testing/run_pytest.py

test-cloud:
	$(PYTHON) scripts/testing/run_cloud_tests.py

clean:
	$(PYTHON) scripts/package.py --clean

ai-refresh:
	$(PYTHON) scripts/hooks/ai_refresh.py

restore:
	$(PYTHON) scripts/restore_project.py
