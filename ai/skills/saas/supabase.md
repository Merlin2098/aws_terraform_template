# Supabase Storage & RLS

## When to use this skill

When configuring Supabase Storage buckets or writing Row Level Security (RLS)
policies for a SaaS application. For schema design, migrations, and audit
fields, see `ai/skills/saas/database.md`. For Auth/JWT/RBAC, see
`ai/skills/saas/auth.md`.

---

## Storage buckets

Create one bucket per logical asset type; do not share a single bucket across
unrelated features.

```sql
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', false)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('attachments', 'attachments', false)
on conflict (id) do nothing;
```

| Bucket | Public | Notes |
|---|---|---|
| `avatars` | No | Served via signed URL or proxied through the API |
| `attachments` | No | Per-tenant/per-record file uploads |
| `public-assets` | Yes | Only for assets safe to expose without auth (logos, marketing) |

Default to **private buckets**. Only mark a bucket `public` when every object
in it is safe for anonymous access.

---

## Object path convention

Prefix object paths with the owning record's identity so storage policies can
match on path segments without a lookup table.

```text
attachments/{user_id}/{record_id}/{filename}
avatars/{user_id}/avatar.png
```

```python
# services/upload_service.py
def build_object_path(user_id: UUID, record_id: UUID, filename: str) -> str:
    safe_name = filename.replace("/", "_")
    return f"{user_id}/{record_id}/{safe_name}"
```

---

## RLS policy patterns

Enable RLS on every table, including `storage.objects` for buckets containing
user data. Per `ai/domains/saas.md`, RLS is a **backup layer** — primary
authorization stays in the service layer — but storage policies are the
exception: Supabase Storage is accessed directly by the client SDK, so RLS is
the *only* enforcement point for object access.

### Table RLS — owner-only access

```sql
alter table appointments enable row level security;

create policy "owner_select" on appointments
  for select
  using (created_by = auth.uid());

create policy "owner_modify" on appointments
  for update using (created_by = auth.uid())
  with check (created_by = auth.uid());
```

### Table RLS — role-based access via `user_profiles`

```sql
create policy "admin_full_access" on appointments
  for all
  using (
    exists (
      select 1 from user_profiles
      where user_profiles.id = auth.uid()
        and user_profiles.role in ('OWNER', 'ADMIN')
    )
  );
```

### Storage RLS — path-prefix ownership

```sql
create policy "users_manage_own_attachments"
  on storage.objects
  for all
  using (
    bucket_id = 'attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id = 'attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );
```

`storage.foldername(name)` splits the object path on `/` — the first segment
must equal the authenticated user's ID, matching the
`{user_id}/{record_id}/{filename}` convention above.

### Storage RLS — public read bucket

```sql
create policy "public_read_assets"
  on storage.objects
  for select
  using (bucket_id = 'public-assets');
```

---

## Upload flow

1. Backend validates the request (file type, size, ownership) in the service
   layer before issuing any storage credentials.
2. Frontend uploads directly to Supabase Storage using the client SDK and the
   user's session JWT — RLS policies enforce the path-prefix rule above.
3. Backend stores the object path (not a signed URL) in the database row.
4. Reads generate a short-lived signed URL on demand.

```ts
// services/storageClient.ts
const path = `${userId}/${recordId}/${file.name}`;

const { error } = await supabase.storage
  .from('attachments')
  .upload(path, file, { upsert: false });

if (error) throw error;
```

```python
# services/attachment_service.py
async def get_signed_url(self, bucket: str, path: str, expires_in: int = 300) -> str:
    result = self.supabase.storage.from_(bucket).create_signed_url(path, expires_in)
    return result["signedURL"]
```

Signed URL TTL: 300 seconds (5 minutes) for download links; never generate a
signed URL with no expiry.

---

## Testing RLS policies

Test policies against the `anon` and `authenticated` roles directly in SQL
before relying on the application layer:

```sql
set role authenticated;
set request.jwt.claims to '{"sub": "11111111-1111-1111-1111-111111111111"}';

select * from appointments; -- should only return rows where created_by matches

reset role;
```

---

## Policies (from domain)

- **Authentication Managed By Supabase** — storage access uses the same
  Supabase session as Auth; do not issue separate storage credentials.
- **Authorization Managed By Application Layer** — RLS on `storage.objects` is
  the exception (direct client access requires it); table RLS remains a
  backup layer behind service-layer checks.
- **No Direct Production Changes** — bucket creation and RLS policies are
  defined in SQL migrations (Alembic), not created ad hoc via the dashboard.

---

## References

- `ai/skills/saas/database.md` — table schema, audit fields, migrations
- `ai/skills/saas/auth.md` — Supabase Auth, JWT, `auth.users`, RBAC roles
- `ai/skills/saas/backend.md` — service layer that issues signed URLs
- `ai/domains/saas.md` — domain overview and all policies
