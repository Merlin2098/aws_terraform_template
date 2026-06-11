ifeq ($(OS),Windows_NT)
PYTHON ?= ./.venv/Scripts/python.exe
UV ?= py -3 -m uv
BOOTSTRAP_PYTHON ?= py -3
else
PYTHON ?= ./.venv/bin/python
UV ?= uv
BOOTSTRAP_PYTHON ?= python3
endif

.PHONY: init uv-init uv-update uv-reset package treemap lint fmt test clean ai-refresh restore

init:
	$(BOOTSTRAP_PYTHON) scripts/run_pip_init.py

uv-init:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py init

uv-update:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py update

uv-reset:
	$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py reset

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

clean:
	$(PYTHON) scripts/package.py --clean

ai-refresh:
	$(PYTHON) scripts/hooks/ai_refresh.py

restore:
	$(PYTHON) scripts/restore_project.py
