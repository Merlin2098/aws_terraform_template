# IAM Least Privilege Pattern

## Principle

Grant only the permissions required for a task.

## Approach

1. Identify required actions
2. Scope to specific resources (ARNs)
3. Avoid wildcards unless necessary

## Example

- s3:GetObject on specific bucket
- logs:CreateLogGroup for CloudWatch

## Terraform pattern

- aws_iam_policy_document
- aws_iam_role
- aws_iam_role_policy_attachment

## Common errors

- Using "*"
- Over-permissioning services
- Not restricting resource scope
