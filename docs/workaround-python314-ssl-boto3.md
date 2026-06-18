# Workaround: boto3 SSL failure on Python 3.14

**Status:** Active — pending upstream fix
**Track:** Review when a new Python 3.14.x patch or botocore release is available
**Introduced:** 2026-06-17

---

## Problem

On Python 3.14, any boto3 call fails with:

```
SSL: CERTIFICATE_VERIFY_FAILED — Basic Constraints of CA cert not marked critical (_ssl.c:1081)
```

Python 3.14 ships OpenSSL 3.x, which enforces stricter X.509 validation. Some AWS
intermediate CA certificates do not mark their `Basic Constraints` extension as
`critical`, which OpenSSL 3 rejects even though the chain is valid under Python ≤3.13,
the AWS CLI, and all major browsers.

The AWS CLI is unaffected because it validates against the **OS trust store** (Windows
Certificate Store / macOS Keychain), which applies the platform's validation rules.

---

## Attempted approach that does NOT work

```python
import truststore
truststore.inject_into_ssl()  # DO NOT USE
```

This patches `ssl.SSLContext` globally. Botocore accesses `SSLContext.options` via
`super(SSLContext, SSLContext).options.__set__(self, value)`, which under the patched
class recurses infinitely:

```
RecursionError: maximum recursion depth exceeded
  File "botocore/httpsession.py", line 561, in options
    super(SSLContext, SSLContext).options.__set__(self, value)
    [Previous line repeated 984 more times]
```

---

## Active workaround

Intercept `botocore.httpsession.create_urllib3_context` — the function botocore
actually uses to build its SSL context — and replace it with a truststore-backed
context. Full certificate verification is preserved; only the trust store source changes.

```python
import ssl
import sys


def enable_os_trust_store() -> bool:
    """Wire botocore to the OS trust store instead of certifi/OpenSSL.

    Only applied on Python 3.14+ where the Basic Constraints regression exists.
    Idempotent — safe to call multiple times.
    Returns True if the OS trust store is active, False if truststore is missing.
    """
    if sys.version_info < (3, 14):
        return True  # native validation works on ≤3.13
    try:
        import truststore
        import botocore.httpsession as hs
    except ImportError:
        return False
    if not getattr(hs, "_truststore_patched", False):
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        hs.create_urllib3_context = lambda *a, **k: ctx
        hs._truststore_patched = True
    return True
```

This helper lives in `tests/aws/conftest.py` (generated per the skill
`ai/skills/aws/aws_smoke_testing.md`) and is called at module import time.

`truststore` is declared in the `cloud` extra in `pyproject.toml`.

**Last-resort fallback:** if `truststore` is not installed on Python 3.14+, the
`aws_client` fixture falls back to `verify=False` with `warnings.warn`. This keeps
connections encrypted but removes server authentication — acceptable only as a stopgap.
Run `uv sync --extra cloud` to restore full verification.

---

## How to validate periodically

Run this script against a live AWS endpoint to check whether the underlying issue
is still present. If it passes without the workaround, the problem has been fixed
upstream.

```python
# scripts/testing/check_ssl_regression.py
import ssl
import socket
import sys

HOST = "sts.us-east-1.amazonaws.com"

print(f"Python {sys.version.split()[0]}, OpenSSL {ssl.OPENSSL_VERSION}")

ctx = ssl.create_default_context()  # certifi, no workaround
try:
    with socket.create_connection((HOST, 443), timeout=10) as s:
        with ctx.wrap_socket(s, server_hostname=HOST):
            pass
    print("NATIVE SSL: OK — workaround no longer needed, remove enable_os_trust_store()")
except ssl.SSLCertVerificationError as e:
    print(f"NATIVE SSL: STILL FAILS — keep workaround active\n  {e}")
```

Run with:

```
.venv/Scripts/python.exe scripts/testing/check_ssl_regression.py   # Windows
.venv/bin/python scripts/testing/check_ssl_regression.py            # Linux/macOS
```

---

## When to remove the workaround

Remove `enable_os_trust_store()` from `conftest.py` and `truststore` from the `cloud`
extra when the check script above outputs `NATIVE SSL: OK`. That indicates Python or
AWS has resolved the underlying incompatibility.

Also update `reusable/incidencias/known-issues.md` and mark the issue **Resolved**.
