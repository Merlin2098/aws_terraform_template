# Terraform Cheat Sheet

Use this flow from PowerShell at the repository root.

This lab expects AWS credentials in `infra\env\.env.credentials`. Keep that file
local only. Do not commit real access keys.

## About the Two Command Styles

Each Terraform step below shows two equivalent, copy-paste-ready blocks:

- **Option A — Inline with `-chdir`**: concise, ideal for short one-liners.
  Terraform treats `infra\` as its working directory, so relative paths like
  `terraform.tfvars` and `tfplan` are resolved inside `infra\`.
- **Option B — `Push-Location` + `try/finally`**: changes the shell's working
  directory to `infra\`, runs the command(s), then returns to the repo root
  even if a command fails. Preferred when commands grow long, when you chain
  several Terraform calls, or when you mix Terraform with other PowerShell
  commands (pipes, redirection, `terraform console`, `terraform import`,
  `terraform state mv`, etc.). Some flag combinations can misbehave with
  `-chdir`; this pattern avoids that.

Pick whichever block fits the moment. The `try { ... } finally { Pop-Location }`
wrapper guarantees you end back at the repo root.

## 1. Load AWS Credentials

```powershell
Get-Content infra\env\.env.credentials | ForEach-Object {
  if ($_ -match "^\s*#" -or $_ -match "^\s*$") { return }

  $name, $value = $_ -split "=", 2
  [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
}
```

Verify only non-secret values:

```powershell
$env:AWS_ACCESS_KEY_ID
$env:AWS_DEFAULT_REGION
```

Avoid printing `AWS_SECRET_ACCESS_KEY`.

## 2. Initialize Terraform

Run this before the first plan, and repeat it when providers, modules, or
backend settings change. This downloads providers and prepares the local
`.terraform` directory.

**Option A — Inline with `-chdir`:**

```powershell
terraform -chdir=infra init
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform init
} finally {
  Pop-Location
}
```

## 3. Create Local Terraform Variables

Create `infra\terraform.tfvars` from the committed example file.

**Option A — Inline (no Terraform involved, plain PowerShell):**

```powershell
Copy-Item infra\terraform.tfvars.example infra\terraform.tfvars
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  Copy-Item terraform.tfvars.example terraform.tfvars
} finally {
  Pop-Location
}
```

Edit `infra\terraform.tfvars` only with non-secret values, such as project name,
environment, region, and tags. This file is ignored by Git.

## 4. Validate Terraform

**Option A — Inline with `-chdir`:**

```powershell
terraform -chdir=infra fmt -check
terraform -chdir=infra validate
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform fmt -check
  terraform validate
} finally {
  Pop-Location
}
```

## 5. Create and Save a Plan

**Option A — Inline with `-chdir`:**

```powershell
terraform -chdir=infra plan -var-file="terraform.tfvars" -out="tfplan"
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform plan -var-file="terraform.tfvars" -out="tfplan"
} finally {
  Pop-Location
}
```

Review the saved plan in human-readable form.

**Option A — Inline with `-chdir`:**

```powershell
terraform -chdir=infra show tfplan
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform show tfplan
} finally {
  Pop-Location
}
```

## 6. Apply the Saved Plan

Apply only the saved plan you reviewed. This creates or changes real AWS
resources.

**Option A — Inline with `-chdir`:**

```powershell
terraform -chdir=infra apply "tfplan"
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform apply "tfplan"
} finally {
  Pop-Location
}
```

## 7. Destroy Lab Resources

First create and review a destroy plan.

**Option A — Inline with `-chdir`:**

```powershell
terraform -chdir=infra plan -destroy -var-file="terraform.tfvars" -out="destroy.tfplan"
terraform -chdir=infra show destroy.tfplan
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform plan -destroy -var-file="terraform.tfvars" -out="destroy.tfplan"
  terraform show destroy.tfplan
} finally {
  Pop-Location
}
```

Then apply the reviewed destroy plan. This deletes the AWS resources managed by
this Terraform state.

**Option A — Inline with `-chdir`:**

```powershell
terraform -chdir=infra apply "destroy.tfplan"
```

**Option B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform apply "destroy.tfplan"
} finally {
  Pop-Location
}
```

## 8. Clean Local Plan Files

After apply or destroy, remove saved plan files:

```powershell
Remove-Item infra\tfplan -ErrorAction SilentlyContinue
Remove-Item infra\destroy.tfplan -ErrorAction SilentlyContinue
```

## 9. Clear Credentials From the Session

When finished, remove AWS credentials from the current PowerShell process:

```powershell
Remove-Item Env:\AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_DEFAULT_REGION -ErrorAction SilentlyContinue
```

Close the terminal window too if you want to fully discard the session.
