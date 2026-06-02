# Terraform Environment Promotion Pattern

## When to use

- Promoting infrastructure from dev to staging or staging to production
- Adding a new environment to an existing project
- Choosing between Terraform workspaces and directory-per-environment

## Core idea

Use a directory-per-environment structure with a shared modules layer. Each
environment has its own state file, its own variable values, and its own
`terraform apply` lifecycle. Environments share module code but nothing else.

---

## Directory-per-environment vs workspaces

| Approach | State isolation | Blast radius | Variable isolation | Recommended |
|---|---|---|---|---|
| Directory per env | Separate state file per dir | Low — apply in one dir cannot affect another | Separate `.tfvars` per dir | Yes |
| Workspaces | Separate workspace in one backend | Higher — all workspaces share the same module version | Same `.tfvars` with workspace conditionals | Only for trivial differences |

Default to directory-per-environment. Workspaces are appropriate only when
environments are nearly identical and the risk of cross-environment blast radius
is acceptable.

---

## Recommended structure

```
infra/
├── modules/               # shared reusable modules
│   ├── pipeline/
│   ├── frontend/
│   └── storage/
└── envs/
    ├── dev/
    │   ├── main.tf        # calls modules with dev variable values
    │   ├── variables.tf
    │   ├── terraform.tfvars   # dev-specific values (gitignored if contains secrets)
    │   ├── backend.tf     # gitignored — points to dev S3 state key
    │   └── outputs.tf
    ├── staging/
    │   └── ...
    └── prod/
        └── ...
```

Each `envs/<env>/main.tf` calls the shared modules with environment-specific inputs:

```hcl
module "pipeline" {
  source       = "../../modules/pipeline"
  environment  = "dev"
  budget_limit = 25
  log_retention_days = 7
  artifact_path = var.artifact_path
  tags         = local.common_tags
}
```

---

## Variable override files

Each environment has its own `terraform.tfvars`. Sensitive values (passwords,
email addresses) must not be committed — inject them via `TF_VAR_*` environment
variables in CI:

```
# infra/envs/dev/terraform.tfvars (committed — no secrets)
environment        = "dev"
budget_limit_usd   = 25
log_retention_days = 7
owner              = "data-team"

# injected by CI, not committed:
# TF_VAR_budget_alert_email=alerts@example.com
```

---

## Immutable artifact promotion

Lambda packages and Glue scripts must be built once and promoted — not
rebuilt per environment. Store artifacts in S3 with a version or commit SHA
in the key:

```
s3://artifacts-bucket/pipeline/v1.2.3/lambda_handler.zip
s3://artifacts-bucket/pipeline/v1.2.3/etl_job.py
```

Each environment's `terraform.tfvars` references the same artifact key:

```hcl
artifact_path = "pipeline/v1.2.3/lambda_handler.zip"
```

Promoting from dev to staging means changing the artifact key in the staging
`terraform.tfvars` to the version that passed dev validation — not rebuilding.

---

## State isolation

Each environment directory has its own `backend.tf` (gitignored) pointing to a
separate S3 key prefix. Never share state between environments:

```hcl
# infra/envs/dev/backend.tf (gitignored)
terraform {
  backend "s3" {
    bucket  = "my-project-tfstate"
    key     = "envs/dev/terraform.tfstate"
    region  = "us-east-1"
    use_lockfile = true
  }
}
```

```hcl
# infra/envs/staging/backend.tf (gitignored)
terraform {
  backend "s3" {
    bucket  = "my-project-tfstate"
    key     = "envs/staging/terraform.tfstate"
    region  = "us-east-1"
    use_lockfile = true
  }
}
```

---

## Pre-promotion checklist

Before running `terraform apply` in the target environment, verify that the
module interface has not changed in a breaking way:

```powershell
cd infra/envs/staging
terraform init
terraform plan -var-file=terraform.tfvars -out=staging.plan
```

If the plan shows unexpected resource replacements (not just value changes),
investigate before applying. A resource replacement in staging may indicate a
module interface change that was not coordinated.

---

## Avoid

- Running `terraform apply` directly in `infra/modules/` — modules are not deployable on their own
- Sharing state files between environments — a failed apply in one environment must not affect another
- Using workspace conditionals (`terraform.workspace == "prod"`) for environment differences — use separate variable files
- Rebuilding Lambda packages per environment — always promote the same artifact
- Hardcoding environment names in module code — pass `environment` as a variable

## See also

- `ai/skills/terraform/state_management.md` — S3 backend and state file hygiene
- `ai/skills/terraform/terraform_stacks.md` — alternative for complex multi-region deployments
- `ai/skills/terraform/modules.md` — module structure and interface design
- `ai/skills/terraform/terraform_governance.md` — per-environment budget and tagging requirements
