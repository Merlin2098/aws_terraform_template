```text
aws_terraform_template/
|-- .claude/
|   |-- settings.json
|   `-- settings.local.json
|-- artifacts/
|   `-- README.md
|-- docs/
|   |-- linux_setup/
|   |   |-- make_cheatlist.md
|   |   |-- README.md
|   |   `-- uv_install.md
|   |-- windows_setup/
|   |   |-- make_cheatlist.md
|   |   |-- make_install.md
|   |   |-- README.md
|   |   |-- terraform_install.md
|   |   `-- uv_install.md
|   |-- terra_principles.md
|   `-- terraform_cheatsheet.md
|-- infra/
|   |-- env/
|   |-- backend.tf.example
|   |-- main.tf
|   |-- outputs.tf
|   |-- providers.tf
|   |-- terraform.tfvars.example
|   `-- variables.tf
|-- scripts/
|   |-- hooks/
|   |   |-- ai_refresh.py
|   |   `-- sync_dependencies.py
|   |-- linux/
|   |   |-- setup_env.sh
|   |   `-- update_venv.sh
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
|   |-- restore_project.py
|   `-- run_uv_sync.py
|-- specs/
|   |-- project/
|   |   `-- README.md
|   |-- rework/
|   |   |-- ADR-FW-001.md
|   |   |-- ADR-FW-002.md
|   |   |-- SPEC-FW-001.md
|   |   |-- SPEC-FW-002.md
|   |   |-- SPEC-FW-003.md
|   |   |-- SPEC-FW-004.md
|   |   |-- SPEC-FW-005.md
|   |   |-- SPEC-FW-015.md
|   |   `-- SPEC-FW-IMPL-PLAN.md
|   |-- template/
|   |   |-- 000-template-spec-format.md
|   |   |-- 001-template-contract.md
|   |   |-- 002-infra-baseline.md
|   |   |-- 003-ai-guidance-layers.md
|   |   `-- 009-cloud-observability-guardrails.md
|   |-- README.md
|   `-- SPEC-017-skills-gap-analysis.md
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
|   |-- test_capability_registry.py
|   |-- test_dependency_graph.py
|   |-- test_example_job.py
|   |-- test_installer.py
|   |-- test_llms_txt.py
|   |-- test_profile.py
|   |-- test_refresh_context.py
|   |-- test_restore_project.py
|   |-- test_script_wrappers.py
|   `-- test_sync_dependencies.py
|-- .gitattributes
|-- .pre-commit-config.yaml
|-- .template-profile
|-- AGENTS.md
|-- CLAUDE.md
|-- install_linux.py
|-- install_windows.py
|-- llms.txt
|-- Makefile
|-- pyproject.toml
|-- README.md
`-- uv.lock
```
