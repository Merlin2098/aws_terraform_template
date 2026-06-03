# SaaS Authentication

## When to use this skill

When implementing authentication and authorization for a SaaS application using Supabase Auth.

---

## Stack

| Concern | Technology |
|---|---|
| Identity provider | Supabase Auth |
| Token format | JWT (RS256, issued by Supabase) |
| Session management | Supabase client SDK |
| Authorization model | RBAC (application layer) |

---

## RBAC roles

| Role | Permissions |
|---|---|
| `OWNER` | Full access; manage users, billing, all records |
| `ADMIN` | Operational admin; all records, no billing |
| `SALES` | Create/manage leads and appointments |
| `SPECIALIST` | Read and update own assigned records |

Store the role in a `user_profiles` table linked to `auth.users`:

```sql
CREATE TABLE user_profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id),
    role        TEXT NOT NULL CHECK (role IN ('OWNER', 'ADMIN', 'SALES', 'SPECIALIST')),
    full_name   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## JWT validation (FastAPI)

Decode and verify the Supabase JWT on every protected request.

```python
# core/security.py
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

bearer = HTTPBearer()

def get_current_user(token=Depends(bearer)) -> dict:
    try:
        payload = jwt.decode(
            token.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
```

---

## Authorization enforcement (service layer)

Authorization decisions live in services, not routers.

```python
# services/appointment_service.py
class AppointmentService:
    async def cancel(self, id: UUID, current_user: dict) -> Appointment:
        appt = await self.repo.get(id)
        role = current_user.get("role")

        if role not in ("OWNER", "ADMIN") and appt.specialist_id != current_user["sub"]:
            raise PermissionError("Not authorized to cancel this appointment")

        return await self.repo.soft_delete(id)
```

---

## Frontend auth flow

1. User signs in via Supabase Auth (email/password or OAuth).
2. Supabase returns `access_token` (JWT) and `refresh_token`.
3. Frontend stores tokens using the Supabase SDK (`supabase.auth.getSession()`).
4. Include the JWT in every API request: `Authorization: Bearer <access_token>`.
5. On 401, call `supabase.auth.refreshSession()` and retry once.

```ts
// lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
);
```

```ts
// services/apiClient.ts — attach token to every request
apiClient.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  if (data.session) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});
```

---

## Protected routes (React)

```tsx
// components/ProtectedRoute.tsx
export function ProtectedRoute({ allowedRoles, children }) {
  const { user, role } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (allowedRoles && !allowedRoles.includes(role)) return <Navigate to="/unauthorized" />;
  return children;
}
```

---

## Policies (from domain)

- **Authentication Managed By Supabase** — do not build custom auth flows.
- **Authorization Managed By Application Layer** — RBAC logic lives in services; do not rely solely on Supabase RLS.

---

## References

- `ai/skills/saas/backend.md` — FastAPI dependency injection for `get_current_user`
- `ai/skills/saas/database.md` — `user_profiles` table and `auth.users` link
- `ai/skills/saas/frontend.md` — frontend session and route protection
- `ai/domains/saas.md` — domain overview and all policies
