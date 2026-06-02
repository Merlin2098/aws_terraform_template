# AWS Cognito Authentication Pattern

## When to use

- Adding user authentication to the web portal
- Configuring a Cognito User Pool and connecting it to API Gateway
- Choosing between the hosted UI and a custom login form

## Core idea

Cognito User Pools handle user registration, sign-in, and token issuance. API
Gateway validates the issued JWTs directly — no custom Lambda authoriser is
needed for standard Cognito flows. The frontend stores tokens in memory (not
localStorage) and uses the `access_token` in the `Authorization` header.

---

## Terraform resources

```hcl
resource "aws_cognito_user_pool" "main" {
  name = "${local.name_prefix}-users"
  tags = local.common_tags

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  auto_verified_attributes = ["email"]

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }
}

resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${local.name_prefix}-frontend-client"
  user_pool_id = aws_cognito_user_pool.main.id

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  # No client secret — browser clients cannot keep secrets
  generate_secret = false

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${local.name_prefix}-auth"
  user_pool_id = aws_cognito_user_pool.main.id
}
```

---

## Hosted UI vs custom login form

| Option | When to use | Trade-offs |
|---|---|---|
| Hosted UI | MVP, internal tools, quick setup | Zero frontend auth code; styling limited to basic CSS; URL redirect visible to users |
| Custom form (Amplify or Cognito SDK) | Customer-facing portal, full UX control | Full control; requires handling token storage, refresh, MFA, error states |

For this project's invoice portal, start with the hosted UI and migrate to a
custom form when UX requirements exceed what the hosted UI can provide.

Hosted UI callback URLs must be registered in the App Client:

```hcl
resource "aws_cognito_user_pool_client" "frontend" {
  # ...
  callback_urls = ["https://${var.cloudfront_domain}/callback"]
  logout_urls   = ["https://${var.cloudfront_domain}/"]
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO"]
}
```

---

## JWT validation in Lambda authorisers

When using a Lambda custom authoriser (instead of the native API Gateway
Cognito authoriser), validate JWTs against the Cognito JWKS endpoint:

```python
from jose import jwt, jwk
from jose.utils import base64url_decode
import urllib.request, json

REGION = "us-east-1"
USER_POOL_ID = "us-east-1_XxXxXx"
APP_CLIENT_ID = "abc123"
JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"

def validate_token(token: str) -> dict:
    with urllib.request.urlopen(JWKS_URL) as response:
        keys = json.loads(response.read())["keys"]
    header = jwt.get_unverified_header(token)
    key = next((k for k in keys if k["kid"] == header["kid"]), None)
    if not key:
        raise ValueError("Public key not found")
    claims = jwt.decode(
        token,
        jwk.construct(key),
        algorithms=["RS256"],
        audience=APP_CLIENT_ID,
    )
    return claims
```

Cache the JWKS response — it does not change frequently and downloading it on
every request adds latency and cost. Never validate JWTs with a shared secret
(`HS256`) — Cognito uses RSA (`RS256`).

---

## API Gateway native Cognito authoriser (HTTP API)

For most cases, skip the Lambda authoriser and use the native JWT authoriser:

```hcl
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  name             = "cognito"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
    audience = [aws_cognito_user_pool_client.frontend.id]
  }
}
```

Attach to specific routes:

```hcl
resource "aws_apigatewayv2_route" "protected" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "POST /upload"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}
```

---

## Frontend auth flow

```javascript
// After successful Cognito sign-in
const { accessToken, idToken, refreshToken } = session.tokens

// Store in memory — NOT localStorage
let _accessToken = accessToken

// Use in API client request interceptor
client.interceptors.request.use(async (config) => {
  config.headers['Authorization'] = `Bearer ${_accessToken}`
  return config
})
```

Refresh the `access_token` before it expires using the `refresh_token`. Do not
store tokens in `localStorage` — they are accessible to any JavaScript running
on the page.

---

## Outputs

Expose all values consumed by the frontend build:

```hcl
output "user_pool_id" {
  value       = aws_cognito_user_pool.main.id
  description = "Cognito User Pool ID — set as VITE_USER_POOL_ID."
}

output "user_pool_client_id" {
  value       = aws_cognito_user_pool_client.frontend.id
  description = "Cognito App Client ID — set as VITE_USER_POOL_CLIENT_ID."
}

output "user_pool_domain" {
  value       = "${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
  description = "Cognito hosted UI domain — used for OAuth redirect flows."
}
```

---

## Avoid

- Validating JWTs with `HS256` — Cognito uses `RS256` only
- Storing tokens in `localStorage` — prefer memory or `sessionStorage` with short lifetime
- Generating a client secret for browser-based clients — browsers cannot keep secrets safe
- Hardcoding User Pool ID or App Client ID — read from `terraform output` into `VITE_*` env vars
- Using a Lambda custom authoriser when the native JWT authoriser covers the use case

## See also

- `ai/skills/aws/api_gateway.md` — JWT authoriser attachment to routes
- `ai/skills/frontend/react_vite_aws.md` — `VITE_USER_POOL_ID` and `VITE_USER_POOL_CLIENT_ID` setup
- `ai/skills/frontend/api_client_patterns.md` — token injection in the request interceptor
- `ai/skills/terraform/iam_least_privilege.md` — scoping Lambda IAM after auth validation
