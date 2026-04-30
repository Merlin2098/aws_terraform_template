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
	$(PYTHON) -m ruff check ai src tests scripts

fmt:
	$(PYTHON) -m ruff format ai src tests scripts

test:
	$(PYTHON) -m pytest

clean:
	$(PYTHON) scripts/package.py --clean

ai-refresh:
	$(PYTHON) scripts/ai_refresh.py --full
