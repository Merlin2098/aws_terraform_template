# AWS Bedrock Permissions Pattern

## When to use

- Deploying any Lambda, Glue job, or Step Functions state that calls Bedrock
- Reviewing IAM roles for pipeline stages that invoke foundation models
- Diagnosing `AccessDeniedException` on first Bedrock call

## Core idea

Bedrock requires two separate prerequisites before any invocation works: IAM
permissions declared in Terraform AND manual model access activation in the AWS
console. Neither alone is sufficient.

---

## IAM actions

The minimum IAM actions required depend on the invocation pattern:

| Action | When required |
|---|---|
| `bedrock:InvokeModel` | All synchronous single-turn calls |
| `bedrock:InvokeModelWithResponseStream` | Streaming responses — separate action, not implied by `InvokeModel` |
| `bedrock:ListFoundationModels` | Smoke tests, model availability checks |
| `bedrock:GetFoundationModel` | Querying model metadata before invocation |

Never use `bedrock:*` as a wildcard — scope to the actions your code actually calls.

### Terraform pattern

```hcl
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    sid    = "BedrockInvokeModel"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-*",
    ]
  }
}

resource "aws_iam_policy" "bedrock_invoke" {
  name   = "${local.name_prefix}-bedrock-invoke"
  policy = data.aws_iam_policy_document.bedrock_invoke.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "bedrock_invoke" {
  role       = aws_iam_role.pipeline_lambda.name
  policy_arn = aws_iam_policy.bedrock_invoke.arn
}
```

Scope the resource ARN to the model family (`anthropic.claude-*`) rather than a
single model ID, so that model upgrades do not require IAM changes.

---

## Model access activation (manual step)

Terraform cannot automate this. Before any Bedrock call will succeed:

1. Open the AWS console → **Amazon Bedrock** → **Model access**
2. Select the region where your Lambda runs
3. Request access for the required model (e.g., Claude 3.5 Sonnet)
4. Wait for access to be granted (usually instant for Anthropic models, up to 1
   business day for some providers)

Without this step, `bedrock:InvokeModel` returns `AccessDeniedException` even
with a correctly scoped IAM policy. Document this step in your project's
`docs/setup.md` — it is the single most common first-deploy failure.

---

## Regional vs cross-region inference ARNs

AWS Bedrock offers two invocation modes with different ARN formats:

| Mode | ARN format | When to use |
|---|---|---|
| Regional | `arn:aws:bedrock:<region>::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0` | Single-region deployments, lowest latency |
| Cross-region inference profile | `arn:aws:bedrock:<region>::inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0` | Higher availability, automatic region failover |

Use the cross-region profile ARN in `bedrock:InvokeModel` calls when the
deployment target is `us-east-1` or `us-west-2`. For other regions, use the
regional ARN.

The IAM resource ARN must match the form used in the actual API call. If the
code calls using the cross-region profile ARN, the IAM policy must also allow
that ARN form.

---

## Smoke test extension

Add a `smoke_bedrock.ps1` (or `.sh`) to `tests/aws/smoke/` that verifies model
access before running the full pipeline:

```powershell
# tests/aws/smoke/smoke_bedrock.ps1
$region = terraform output -raw aws_region
aws bedrock list-foundation-models --region $region --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20241022-v2:0']" --output table
if ($LASTEXITCODE -ne 0) { Write-Error "Bedrock model access check failed"; exit 1 }
Write-Host "Bedrock access OK"
```

Read the region from `terraform output` — never hardcode it.

---

## Avoid

- Using `bedrock:*` or `Resource: "*"` — always scope to model ARNs
- Deploying without first activating model access in the console
- Mixing regional and cross-region profile ARNs in the same IAM policy
- Hardcoding model IDs in IAM policies — use `anthropic.claude-*` wildcard to allow family upgrades

## See also

- `ai/skills/terraform/iam_least_privilege.md` — IAM scoping principles
- `ai/skills/python/bedrock_client.md` — invocation patterns and retry handling
- `ai/skills/terraform/terraform_governance.md` — Bedrock cost alert setup
