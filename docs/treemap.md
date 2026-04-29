```text
aws_terraform_template/
|-- artifacts/
|   `-- README.md
|-- docs/
|-- infra/
|   |-- main.tf
|   |-- outputs.tf
|   |-- providers.tf
|   |-- terraform.tfvars.example
|   `-- variables.tf
|-- scripts/
|   |-- generate_treemap.py
|   |-- package.py
|   `-- sync_requirements.py
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
|   `-- test_example_job.py
|-- .pre-commit-config.yaml
|-- AGENTS.md
|-- main.py
|-- Makefile
|-- README.md
`-- requirements.txt
```
