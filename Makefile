ifeq ($(OS),Windows_NT)
PYTHON ?= ./.venv/Scripts/python.exe
else
PYTHON ?= ./.venv/bin/python
endif

.PHONY: init package treemap lint fmt test clean

init:
	$(PYTHON) -m pip install -r requirements.txt

package:
	$(PYTHON) scripts/package.py

treemap:
	$(PYTHON) scripts/generate_treemap.py

lint:
	$(PYTHON) -m ruff check src tests scripts

fmt:
	$(PYTHON) -m ruff format src tests scripts

test:
	$(PYTHON) -m pytest

clean:
	$(PYTHON) scripts/package.py --clean
