```text
aws_terraform_template/
|-- artifacts/
|   `-- README.md
|-- docs/
|   |-- terraform_cheatsheet.md
|   `-- windows_setup.md
|-- infra/
|   |-- env/
|   |-- modules/
|   |-- main.tf
|   |-- outputs.tf
|   |-- providers.tf
|   |-- terraform.tfvars.example
|   `-- variables.tf
|-- scripts/
|   |-- hooks/
|   |   |-- ai_refresh.py
|   |   `-- sync_requirements.py
|   |-- testing/
|   |   |-- run_pytest.py
|   |   |-- run_ruff_check.py
|   |   `-- run_ruff_format.py
|   |-- generate_treemap.py
|   `-- package.py
|-- src/
|   |-- config/
|   |   `-- job_config.yaml
|   |-- contracts/
|   |   `-- orders_contract.json
|   |-- jobs/
|   |   |-- __init__.py
|   |   `-- example_job.py
|   |-- transformations/
|   |   `-- orders_to_curated.sql
|   `-- __init__.py
|-- tests/
|   |-- test_example_job.py
|   |-- test_installer.py
|   |-- test_refresh_context.py
|   `-- test_script_wrappers.py
|-- .pre-commit-config.yaml
|-- AGENTS.md
|-- install_linux.py
|-- install_windows.py
|-- Makefile
|-- README.md
|-- requirements.cloud.txt
|-- requirements.dev.txt
`-- requirements.local.txt
```
