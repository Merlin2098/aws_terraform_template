```text
richi_toolkit/
|-- .claude/
|   `-- settings.json
|-- artifacts/
|   `-- README.md
|-- docs/
|   |-- adr/
|   |   |-- 0001-behavioral-skill-class.md
|   |   `-- 0002-lambda-packaging-strategy.md
|   |-- linux_setup/
|   |   |-- make_cheatlist.md
|   |   |-- README.md
|   |   `-- uv_install.md
|   |-- windows_setup/
|   |   |-- make_cheatlist.md
|   |   |-- make_install.md
|   |   |-- README.md
|   |   |-- template_versioning.md
|   |   |-- terraform_install.md
|   |   `-- uv_install.md
|   |-- terra_principles.md
|   |-- terraform_cheatsheet.md
|   `-- workaround-python314-ssl-boto3.md
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
|   |   |-- check_ssl_regression.py
|   |   |-- run_cloud_tests.py
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
|   |-- legacy/
|   |   |-- rework/
|   |   |   |-- ADR-FW-001.md
|   |   |   |-- ADR-FW-002.md
|   |   |   |-- ADR-FW-003.md
|   |   |   |-- SPEC-FW-001.md
|   |   |   |-- SPEC-FW-002.md
|   |   |   |-- SPEC-FW-003.md
|   |   |   |-- SPEC-FW-004.md
|   |   |   |-- SPEC-FW-005.md
|   |   |   |-- SPEC-FW-015.md
|   |   |   |-- SPEC-FW-016.md
|   |   |   `-- SPEC-FW-IMPL-PLAN.md
|   |   |-- SPEC-017-skills-gap-analysis.md
|   |   `-- SPEC-018-shell-automation-skill-pack.md
|   |-- project/
|   |   |-- README.md
|   |   `-- SPEC-019-toolkit-review-gitbash-multilang.md
|   `-- README.md
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
|   |-- aws/
|   |   `-- aws_session.py
|   |-- test_capability_registry.py
|   |-- test_dependency_graph.py
|   |-- test_example_job.py
|   |-- test_install_entrypoints.py
|   |-- test_installer.py
|   |-- test_profile.py
|   |-- test_project_profile.py
|   |-- test_refresh_context.py
|   |-- test_restore_project.py
|   |-- test_script_wrappers.py
|   `-- test_sync_dependencies.py
|-- .gitattributes
|-- .pre-commit-config.yaml
|-- .template-profile.yaml
|-- AGENTS.md
|-- CLAUDE.md
|-- install.py
|-- Makefile
|-- pyproject.toml
|-- README.md
`-- uv.lock
```
