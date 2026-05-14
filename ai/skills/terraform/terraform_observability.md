# Terraform Observability Pattern

## When to use

- Adding any AWS service that produces logs
- Defining new Terraform modules
- Reviewing infrastructure for SPEC-009 compliance

## Core idea

Every deployable service must explicitly declare its CloudWatch log group in
Terraform. Never rely on AWS auto-created log groups — they are not owned by
Terraform and cannot be managed (retention, tags, deletion).

## Mandatory outputs

Every module must expose at minimum:

```hcl
output "resource_arn"    {}
output "resource_name"   {}
output "log_group_name"  {}
```

## Pattern: explicit log group declaration

```hcl
resource "aws_cloudwatch_log_group" "my_service" {
  name              = "/aws/my-service/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}
```

Always:
- Use a structured name path: `/aws/<service-type>/<name-prefix>`
- Apply `local.common_tags` (includes `Project`, `Environment`, `Owner`, `ManagedBy`, `CostCenter`)
- Set `retention_in_days` from a variable — never omit or hardcode

## Retention standard (SPEC-009 §5.3)

| Environment        | Retention        |
|--------------------|------------------|
| demo / lab / dev   | 7 days           |
| production         | per compliance requirements |

Variable declaration:

```hcl
variable "log_retention_days" {
  description = "CloudWatch log retention in days. Use 7 for demos/labs."
  type        = number
  default     = 7
}
```

## IAM permissions for log writing

The execution role must have explicit permissions scoped to the log group ARN:

```hcl
data "aws_iam_policy_document" "cloudwatch_logs_access" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]
    resources = ["${aws_cloudwatch_log_group.my_service.arn}:*"]
  }
}

resource "aws_iam_role_policy" "cloudwatch_logs_access" {
  name   = "${local.name_prefix}-cloudwatch-logs-access"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.cloudwatch_logs_access.json
}
```

Never use `Resource = "*"` for log actions.

## Service-specific log group naming

| Service        | Recommended name path                          |
|----------------|------------------------------------------------|
| Glue           | `/aws-glue/jobs/${local.name_prefix}`          |
| Lambda         | `/aws/lambda/${local.name_prefix}`             |
| Step Functions | `/aws/states/${local.name_prefix}`             |
| Data jobs      | `/aws/data-jobs/${local.name_prefix}`          |
| Custom         | `/aws/<service>/${local.name_prefix}`          |

## Outputs to always declare

```hcl
output "log_group_name" {
  description = "CloudWatch log group name."
  value       = aws_cloudwatch_log_group.my_service.name
}

output "log_group_arn" {
  description = "CloudWatch log group ARN."
  value       = aws_cloudwatch_log_group.my_service.arn
}
```

## Avoid

- Auto-created log groups (not in Terraform state)
- Omitting `retention_in_days` (results in infinite retention and runaway cost)
- Using `logs:*` with `Resource = "*"` (violates least privilege)
- Naming log groups without the environment prefix (creates collision risk across environments)
