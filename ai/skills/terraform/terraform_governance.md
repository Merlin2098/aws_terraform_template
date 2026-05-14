# Terraform Governance Pattern

## When to use

- Creating or reviewing any Terraform infrastructure
- Adding new environments or modules
- SPEC-009 compliance review

## Core idea

Every deployable environment must have: mandatory tags on all resources, at
least one AWS Budget with alerting, and an explicit versioning decision.
No environment should exist without cost governance.

---

## Tagging enforcement

All resources must carry these five tags via `local.common_tags`:

```hcl
locals {
  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      Owner       = var.owner
      ManagedBy   = "Terraform"
      CostCenter  = var.cost_center
    }
  )
}
```

Required variables:

```hcl
variable "cost_center" {
  description = "Cost center for budget allocation and cost reporting."
  type        = string
  default     = "engineering"
}
```

Never create a resource without `tags = local.common_tags`.

---

## Budget governance

Every project must declare at least one `aws_budgets_budget`:

```hcl
resource "aws_budgets_budget" "monthly" {
  name              = "${local.name_prefix}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = tostring(var.budget_limit_usd)
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  cost_filter {
    name   = "TagKeyValue"
    values = ["user:Project$${var.project_name}"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_email != "" ? [var.budget_alert_email] : []
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.budget_alert_email != "" ? [var.budget_alert_email] : []
  }
}
```

Budget alert via SNS (optional, activated when email is provided):

```hcl
resource "aws_sns_topic" "budget_alerts" {
  count = var.budget_alert_email != "" ? 1 : 0
  name  = "${local.name_prefix}-budget-alerts"
  tags  = local.common_tags
}

resource "aws_sns_topic_subscription" "budget_email" {
  count     = var.budget_alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.budget_alerts[0].arn
  protocol  = "email"
  endpoint  = var.budget_alert_email
}
```

Required variables:

```hcl
variable "budget_limit_usd" {
  description = "Monthly budget limit in USD."
  type        = number
  default     = 25
}

variable "budget_alert_email" {
  description = "Email for budget alerts. Empty to skip SNS creation."
  type        = string
  default     = ""
}
```

---

## Versioning policy (SPEC-009 §8.3)

S3 versioning must be **disabled by default**. Enable only when explicitly
requested and documented.

```hcl
variable "enable_artifact_bucket_versioning" {
  description = "Enable S3 versioning. Off by default — activating it incurs storage costs and complicates destroy."
  type        = bool
  default     = false
}
```

Rationale: versioning causes hidden costs, storage accumulation, and
`terraform destroy` complexity in demo/lab environments.

---

## Drift management process (SPEC-009 §8.2)

If a resource is modified manually through the AWS Console:

1. Detect drift: `terraform plan` will show the diff
2. Remove from state: `terraform state rm <resource_address>`
3. Re-import: `terraform import <resource_address> <aws_id>`
4. Update Terraform code to match the real state
5. Run `terraform plan` again to confirm zero diff

Never delete `terraform.tfstate` to resolve drift — this orphans infrastructure.

---

## State protection (SPEC-009 §8.1)

- Remote backend is mandatory (S3 with native locking — see SPEC-008)
- Never run `rm terraform.tfstate`
- State modifications require agent approval (see `AGENTS.md` approval boundaries)

---

## Avoid

- Resources without `tags = local.common_tags`
- Deploying without an `aws_budgets_budget`
- Enabling S3 versioning without explicit justification
- Resolving drift by deleting state files
- Using `terraform apply` without a prior `terraform plan` review
