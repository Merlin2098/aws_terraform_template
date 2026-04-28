PYTHON ?= python
TERRAFORM ?= terraform
TF_DIR ?= infra

.PHONY: init package lint fmt test deploy clean

init:
	$(PYTHON) -m pip install -r requirements.txt

package:
	$(PYTHON) scripts/package.py

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
