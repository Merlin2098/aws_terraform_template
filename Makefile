ifeq ($(OS),Windows_NT)
PYTHON ?= ./.venv/Scripts/python.exe
else
PYTHON ?= ./.venv/bin/python
endif

.PHONY: init package treemap lint fmt test clean ai-refresh

init:
	$(PYTHON) -m pip install -r requirements.local.txt -r requirements.dev.txt

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
