# SaaS Domains, DNS & Email

## When to use this skill

When configuring DNS records, TLS, or transactional email for a SaaS
application's custom domain — whether the app is hosted on Railway/Vercel
(`ai/skills/saas/deployment.md`) or a VPS (`ai/skills/saas/vps.md`).

---

## DNS provider

Use Cloudflare as the DNS provider regardless of where the application is
hosted: it gives a consistent place to manage records, free DNS-level DDoS
protection, and (optionally) a CDN/proxy layer in front of the app.

| Record purpose | Type | Example |
|---|---|---|
| Frontend (apex) | `A` or `ALIAS`/`CNAME` (flattened) | `example.com -> <host IP or platform target>` |
| Frontend (www) | `CNAME` | `www.example.com -> example.com` |
| API subdomain | `A` or `CNAME` | `api.example.com -> <host IP or platform target>` |
| Email sending | `TXT`, `MX`, `CNAME` | see Email section |

---

## Apex vs subdomain

- Prefer serving the app from `app.example.com` and the API from
  `api.example.com`, with `example.com` (apex) reserved for marketing or a
  redirect to `app.example.com`.
- If the platform requires an apex record (`example.com` with no subdomain),
  use Cloudflare's CNAME flattening (`CNAME` at the apex is proxied as if it
  were an `A`/`AAAA` record) — do not use raw `A` records pointing at
  managed-platform IPs, since those IPs can change without notice.

---

## Cloudflare proxy mode

| Mode | When to use |
|---|---|
| Proxied (orange cloud) | Default for `app.`/`www.`/apex — gets Cloudflare TLS, caching, DDoS protection |
| DNS only (grey cloud) | Required when the origin platform issues its own TLS cert tied to the hostname (e.g., some PaaS custom-domain flows) and validates via direct connection |

When deploying to a VPS (`ai/skills/saas/vps.md`), proxied mode is safe —
Cloudflare terminates TLS to the visitor and connects to the VPS over
Cloudflare's network. When using Let's Encrypt's HTTP-01 challenge on the VPS
directly, temporarily set the record to "DNS only" during initial certificate
issuance if Cloudflare's proxy interferes with the challenge, then re-enable
proxying.

---

## TLS

| Hosting | TLS source |
|---|---|
| Railway / Vercel | Platform-managed certificate (automatic once DNS is verified) |
| VPS | Let's Encrypt via Certbot (see `ai/skills/saas/vps.md`) |
| Cloudflare proxied | Cloudflare edge certificate (additional layer in front of origin TLS) |

Set Cloudflare's SSL/TLS mode to **Full (strict)** when the origin has a valid
certificate (Let's Encrypt or platform-managed) — never use "Flexible" mode in
production, since it leaves the Cloudflare-to-origin hop unencrypted.

---

## Email — transactional sending

Use a dedicated transactional email provider (e.g., Resend, Postmark, SES) —
do not send application email directly from the app server's IP.

### Required DNS records

```text
# SPF — authorize the provider to send on your behalf
example.com.       TXT   "v=spf1 include:_spf.<provider>.com ~all"

# DKIM — provider-issued selector and public key
<selector>._domainkey.example.com.   CNAME   <selector>.dkim.<provider>.com

# DMARC — policy for unauthenticated mail
_dmarc.example.com.   TXT   "v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@example.com"
```

- Start DMARC with `p=none` (monitor only) for at least one reporting cycle,
  then move to `p=quarantine` once SPF/DKIM are confirmed passing for all
  legitimate senders.
- One SPF record per domain — if multiple services send mail (e.g., the app
  provider and a marketing tool), merge `include:` mechanisms into a single
  `TXT` record; multiple SPF records are invalid per RFC 7208.

### Sending domain vs root domain

Send transactional email from a subdomain (e.g., `mail.example.com` or
`notifications.example.com`) rather than the root domain. This isolates
sender reputation: a deliverability problem with transactional mail does not
affect the root domain's reputation for other purposes (e.g., a future
marketing domain).

---

## Verification checklist (new domain)

- [ ] Apex and `www`/`app` records point at the correct target (CNAME
      flattening if apex).
- [ ] `api.` subdomain configured if the API is on a separate host/path.
- [ ] TLS mode set to Full (strict) if Cloudflare-proxied.
- [ ] SPF, DKIM, DMARC records added for the transactional email provider.
- [ ] DMARC starts at `p=none`; revisit after the first reporting cycle.
- [ ] Certificate issuance/renewal verified (`certbot certificates` on VPS, or
      platform dashboard shows "Active"/"Valid").

---

## Policies (from domain)

- **No Secrets In Source Code** — DNS provider API tokens (if used for
  automation) are stored as environment variables / secret manager entries,
  never committed.
- **Deploy Must Be Reproducible** — DNS record changes are documented in this
  file or an equivalent runbook so they can be reproduced for a new
  environment (e.g., staging domain).

---

## References

- `ai/skills/saas/deployment.md` — Railway/Vercel custom domain setup
- `ai/skills/saas/vps.md` — Nginx + Let's Encrypt TLS on a self-managed host
- `ai/domains/saas.md` — domain overview and all policies
