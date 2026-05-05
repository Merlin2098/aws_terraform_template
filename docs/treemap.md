```text
aws_terraform_template/
|-- artifacts/
|   `-- README.md
|-- docs/
|   |-- windows_setup/
|   |   |-- make_install.md
|   |   |-- README.md
|   |   `-- uv_install.md
|   `-- terraform_cheatsheet.md
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
|   |   `-- sync_dependencies.py
|   |-- testing/
|   |   |-- run_pytest.py
|   |   |-- run_ruff_check.py
|   |   `-- run_ruff_format.py
|   |-- windows/
|   |   |-- run_make.ps1
|   |   |-- setup_env.ps1
|   |   `-- update_venv.ps1
|   |-- generate_treemap.py
|   |-- package.py
|   |-- run_pip_init.py
|   `-- run_uv_sync.py
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
|   |-- test_script_wrappers.py
|   `-- test_sync_dependencies.py
|-- .gitattributes
|-- .pre-commit-config.yaml
|-- AGENTS.md
|-- install_linux.py
|-- install_windows.py
|-- Makefile
|-- pyproject.toml
|-- README.md
|-- requirements.cloud.txt
|-- requirements.dev.txt
|-- requirements.local.txt
`-- uv.lock
```
