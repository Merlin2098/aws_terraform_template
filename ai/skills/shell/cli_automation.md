# CLI Automation (Git, Terraform, Docker, AWS, Azure)

## When to use

- Writing scripts that orchestrate CLI tools: `git`, `terraform`, `docker`, `aws`, `az`
- Building DevOps automation scripts (deploy pipelines, CI steps, maintenance jobs)
- Generating a Bash CLI workflow (default) with a PowerShell equivalent only when the fallback is actually needed — see `ai/domains/shell.md` §Shell precedence

For the *service-level behaviour* (what Lambda does, how S3 buckets work, IAM policy design), consult:
- `ai/skills/aws/` — AWS service patterns
- `ai/skills/terraform/` — Terraform module/state/governance patterns

This skill covers **how to script CLI invocations safely**.

---

## Shared principles for all CLIs

1. **Validate before destructive operations** — always run a read/dry-run first
2. **Require explicit confirmation** for operations that delete, apply, or deploy (see `ai/skills/shell/script_security.md`)
3. **Check exit codes** — never pipe through `|| true` silently
4. **Capture and log output** — redirect stdout/stderr to logs for auditability
5. **Pass credentials via environment variables** — never in command arguments or scripts

---

## Git

```bash
# Safe clone with error check
git clone "$REPO_URL" "$TARGET_DIR" || die "git clone failed"

# Pull with rebase — avoids spurious merge commits
git pull --rebase origin main

# Tag and push (requires explicit intent)
git tag -a "v$VERSION" -m "Release $VERSION"
git push origin "v$VERSION"
```

**Destructive git commands (`reset --hard`, `push --force`, `branch -D`):**
- Always confirm with the user before running
- Document the reason in the script header
- Prefer `--force-with-lease` over `--force` for remote pushes

---

## Terraform

Always follow: `validate → fmt → plan → (review) → apply`

```bash
#!/usr/bin/env bash
set -euo pipefail
CHDIR="${TF_CHDIR:-infra}"

terraform -chdir="$CHDIR" init    -input=false
terraform -chdir="$CHDIR" validate
terraform -chdir="$CHDIR" fmt     -check -recursive

# plan saves to file to ensure apply uses identical plan
terraform -chdir="$CHDIR" plan    -input=false -out=tfplan

# apply requires human approval — never run unattended in production
# (see AGENTS.md "Approval Boundaries")
echo "Review the plan above. Run: terraform -chdir=$CHDIR apply tfplan"
```

PowerShell equivalent:

```powershell
$chdir = $env:TF_CHDIR ?? 'infra'
terraform -chdir=$chdir init     -input=false
terraform -chdir=$chdir validate
terraform -chdir=$chdir fmt      -check -recursive
terraform -chdir=$chdir plan     -input=false -out=tfplan
Write-Host "Review the plan above. Run: terraform -chdir=$chdir apply tfplan"
```

`terraform destroy` and `terraform apply` always require explicit user approval (AGENTS.md §Approval Boundaries). Never automate them without a documented approval gate.

---

## Docker

```bash
# Build with explicit tag
docker build -t "$IMAGE:$TAG" -f Dockerfile .

# Run with resource limits
docker run --rm \
    --memory=512m --cpus=1 \
    -e APP_ENV="$ENV" \
    "$IMAGE:$TAG"

# Stop and remove container
CONTAINER_ID=$(docker ps -q --filter "name=$CONTAINER_NAME")
if [[ -n "$CONTAINER_ID" ]]; then
    docker stop "$CONTAINER_ID"
    docker rm   "$CONTAINER_ID"
fi

# Tail logs
docker logs --tail=100 -f "$CONTAINER_NAME"
```

---

## AWS CLI

```bash
# Always confirm identity first
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
log "Operating as account: $AWS_ACCOUNT in region: ${AWS_DEFAULT_REGION:-us-east-1}"

# Read terraform outputs for resource names (never hardcode ARNs)
OUTPUTS=$(terraform -chdir=infra output -json)
BUCKET=$(echo "$OUTPUTS" | jq -r '.artifact_bucket_name.value')

# S3 copy with validation
aws s3 cp "$LOCAL_FILE" "s3://$BUCKET/$KEY" \
    --sse aws:kms \
    --expected-bucket-owner "$AWS_ACCOUNT"
```

PowerShell equivalent:

```powershell
$account = (aws sts get-caller-identity | ConvertFrom-Json).Account
$outputs = terraform -chdir=infra output -json | ConvertFrom-Json
$bucket  = $outputs.artifact_bucket_name.value
aws s3 cp $LocalFile "s3://$bucket/$Key" --sse aws:kms --expected-bucket-owner $account
```

Never embed AWS credentials in scripts. Use IAM roles, `AWS_PROFILE`, or environment variables set outside the script.

---

## Azure CLI

```bash
# Confirm active subscription
az account show --query '{name:name, id:id}' -o json | jq .

# Resource group operations
az group create  --name "$RG" --location "$LOCATION"
az group list    --output table
az group delete  --name "$RG" --yes  # requires explicit --yes; add confirmation prompt in scripts
```

---

## Best practices

- Print the CLI version in CI scripts (`terraform version`, `aws --version`) for reproducibility
- Use `--output json` and parse with `jq` (Bash) or `ConvertFrom-Json` (PS) — never parse text output with `awk`/`sed`
- Wrap multi-step CLI sequences in a function with a single `set -euo pipefail` scope
- In CI, set `TF_IN_AUTOMATION=true` to suppress Terraform interactive prompts

## Avoid

- Hardcoding account IDs, ARNs, or bucket names — read from `terraform output` or env vars
- Running `terraform apply` or `az group delete` without a review step
- Using `--force` flags without documenting why
- Mixing credential management into automation scripts (use IAM roles or external secret stores)
