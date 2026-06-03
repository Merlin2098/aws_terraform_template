# SaaS Database

## When to use this skill

When designing or modifying PostgreSQL schemas for a SaaS application hosted on Supabase.

---

## Stack

| Concern | Technology |
|---|---|
| Database | PostgreSQL 15+ |
| Hosting | Supabase |
| Migrations | Alembic |
| ORM | SQLAlchemy 2.x |

---

## Mandatory table fields

Every table must include these audit and soft-delete columns:

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
created_by  UUID REFERENCES auth.users(id),
deleted_at  TIMESTAMPTZ  -- NULL means active; soft delete only
```

Add a `updated_at` trigger on every table:

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_updated_at
BEFORE UPDATE ON <table>
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Soft delete

Never hard-delete user data. Use `deleted_at` timestamp.

```python
# SQLAlchemy filter for active records
stmt = select(Appointment).where(Appointment.deleted_at.is_(None))

# Soft delete
async def soft_delete(self, id: UUID) -> None:
    await self.session.execute(
        update(Appointment)
        .where(Appointment.id == id)
        .values(deleted_at=datetime.utcnow())
    )
```

---

## Migrations (Alembic)

- One migration per logical change — do not bundle unrelated schema changes.
- Never modify an existing migration file once it has been applied to any environment.
- Migration file names: `YYYYMMDD_HHMM_<short_description>.py`.

```bash
alembic revision --autogenerate -m "add_appointments_table"
alembic upgrade head
```

Always test rollback before merging:

```bash
alembic downgrade -1
alembic upgrade head
```

---

## Indexes

Add indexes for columns used in `WHERE`, `ORDER BY`, or `JOIN` predicates.

```sql
-- Foreign keys
CREATE INDEX idx_appointments_lead_id ON appointments(lead_id);

-- Soft-delete filter (partial index — only active rows)
CREATE INDEX idx_appointments_active ON appointments(id)
WHERE deleted_at IS NULL;

-- Common filter combinations
CREATE INDEX idx_appointments_date_status ON appointments(scheduled_at, status)
WHERE deleted_at IS NULL;
```

---

## Constraints

Prefer database-level constraints over application-only validation.

```sql
-- Enum via CHECK
ALTER TABLE appointments
ADD CONSTRAINT chk_status CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED'));

-- No overlapping appointments for the same specialist (exclusion constraint)
ALTER TABLE appointments
ADD CONSTRAINT no_overlap EXCLUDE USING gist (
    specialist_id WITH =,
    tstzrange(scheduled_at, end_at) WITH &&
) WHERE (deleted_at IS NULL);
```

---

## Supabase specifics

- Use `auth.users` as the identity table; do not replicate auth columns.
- Row Level Security (RLS) is a backup layer — primary authorization lives in the application layer.
- Enable RLS on all tables but keep policies simple; complex rules belong in services.
- Use Supabase Storage for file uploads, not database BLOBs.

---

## Policies (from domain)

- **Soft Delete By Default** — use `deleted_at`; never hard-delete.
- **Audit Fields Mandatory** — `created_at`, `updated_at`, `created_by` on every table.
- **No Direct Production Changes** — all schema changes through Alembic migrations.

---

## References

- `ai/skills/saas/backend.md` — repository pattern that queries these tables
- `ai/skills/saas/auth.md` — auth.users integration and RBAC
- `ai/domains/saas.md` — domain overview and all policies
