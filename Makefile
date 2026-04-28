ifeq ($(OS),Windows_NT)
PYTHON ?= ./.venv/Scripts/python.exe
else
PYTHON ?= ./.venv/bin/python
endif

TERRAFORM ?= terraform
TF_DIR ?= infra

.PHONY: init package treemap lint fmt test deploy clean

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

deploy: package
	$(TERRAFORM) -chdir=$(TF_DIR) init
	$(TERRAFORM) -chdir=$(TF_DIR) apply

clean:
	$(PYTHON) scripts/package.py --clean
