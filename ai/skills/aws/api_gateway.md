# AWS API Gateway Pattern

## When to use

- Creating or modifying API endpoints that front Lambda functions
- Choosing between REST API and HTTP API
- Configuring CORS, authorisers, or throttling
- Wiring API Gateway access logging to CloudWatch

## Core idea

HTTP API is the default choice for Lambda proxy integrations in this project —
it is cheaper, lower latency, and simpler to configure. Use REST API only when
you need features that HTTP API does not support.

---

## REST API vs HTTP API

| Capability | HTTP API | REST API |
|---|---|---|
| Lambda proxy integration | Yes | Yes |
| Cognito JWT authoriser | Yes | Yes (via Cognito authoriser) |
| IAM auth (`AWS_IAM`) | Yes | Yes |
| Lambda custom authoriser | Yes | Yes |
| API keys / usage plans | No | Yes |
| WAF integration | No | Yes |
| Request/response mapping templates | No | Yes |
| Default cost (per 1M calls) | ~$1 | ~$3.50 |

**Default: HTTP API.** Switch to REST API only when WAF, usage plans, or
mapping templates are explicitly required.

---

## Lambda proxy integration

In proxy mode, API Gateway passes the entire request to Lambda without
transformation. Lambda must return a specific envelope:

```python
def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "ok"}),
    }
```

The `body` field must be a string — JSON-encode it before returning.

---

## Terraform resources (HTTP API)

```hcl
resource "aws_apigatewayv2_api" "main" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"
  tags          = local.common_tags

  cors_configuration {
    allow_origins = [var.frontend_origin]  # e.g. "https://d1234.cloudfront.net"
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.handler.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "post_upload" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /upload"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
  tags        = local.common_tags

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
```

---

## Access logging

Declare an explicit CloudWatch log group for API Gateway access logs. Follow
the observability pattern from `terraform_observability.md`:

```hcl
resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigateway/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}
```

Expose `log_group_name` and `log_group_arn` as module outputs.

---

## Throttling

HTTP API default: no throttle (unlimited requests). Set stage-level throttling
to protect downstream Lambda and avoid runaway cost:

```hcl
resource "aws_apigatewayv2_stage" "default" {
  # ...
  default_route_settings {
    throttling_rate_limit  = 100  # requests/second
    throttling_burst_limit = 200  # concurrent requests
  }
}
```

---

## Authoriser options

| Type | When to use |
|---|---|
| Cognito JWT | User-authenticated web portal — see `aws/cognito_auth.md` |
| `AWS_IAM` | Service-to-service calls authenticated with SigV4 |
| Lambda custom | Complex auth logic not covered by JWT or IAM |
| API key | Server-to-server calls where IAM is impractical (REST API only) |

Cognito JWT authoriser (HTTP API):

```hcl
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  name             = "cognito-authorizer"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.user_pool_id}"
    audience = [var.user_pool_client_id]
  }
}
```

---

## Outputs

```hcl
output "api_endpoint" {
  value       = aws_apigatewayv2_api.main.api_endpoint
  description = "Base URL for the API Gateway endpoint."
}

output "log_group_name" {
  value       = aws_cloudwatch_log_group.api_access.name
  description = "CloudWatch log group name for API access logs."
}

output "log_group_arn" {
  value       = aws_cloudwatch_log_group.api_access.arn
  description = "CloudWatch log group ARN for API access logs."
}
```

---

## CORS notes

- For HTTP API: configure CORS at the API level — do not add `Access-Control-*`
  headers manually in Lambda responses; they conflict with the API-level config
- For REST API: add a mock OPTIONS method or use a Lambda that returns the
  correct headers; the console "Enable CORS" button generates this but does not
  produce Terraform-friendly code — always configure in HCL

---

## Avoid

- Leaving throttling unconfigured — the default has no limit
- Returning non-string `body` in Lambda proxy responses — causes `502 Bad Gateway`
- Hardcoding the API endpoint URL in frontend code — read from `terraform output`
- Using REST API when HTTP API capabilities are sufficient — REST API costs 3× more
- Manually configuring CORS via `Access-Control-*` headers in Lambda when HTTP API CORS config is active

## See also

- `ai/skills/aws/lambda_functions.md` — Lambda configuration and handler structure
- `ai/skills/terraform/terraform_observability.md` — log group retention and tagging pattern
- `ai/skills/terraform/iam_least_privilege.md` — Lambda execution role scoping
- `ai/skills/aws/cognito_auth.md` — JWT authoriser setup
- `ai/skills/frontend/react_vite_aws.md` — consuming the API endpoint from the frontend
