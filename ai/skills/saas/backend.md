# SaaS Backend

## When to use this skill

When building REST APIs for a SaaS application with FastAPI, SQLAlchemy, and Pydantic.

---

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Database | PostgreSQL via Supabase (see `ai/skills/saas/database.md`) |

---

## Layer architecture

```
Router (HTTP boundary)
  └── Service (business logic)
        └── Repository (data access)
```

No layer may skip another. Routers call services. Services call repositories.
Business logic must not appear in routers or repositories.

---

## Project structure

```
app/
├── api/
│   └── v1/
│       ├── router.py          # mounts all sub-routers
│       └── endpoints/
│           ├── appointments.py
│           └── leads.py
├── services/
│   ├── appointment_service.py
│   └── lead_service.py
├── repositories/
│   ├── appointment_repo.py
│   └── lead_repo.py
├── models/
│   └── appointment.py         # SQLAlchemy models
├── schemas/
│   └── appointment.py         # Pydantic request/response schemas
├── core/
│   ├── config.py              # settings via pydantic-settings
│   ├── database.py            # async engine + session factory
│   └── security.py            # JWT decode, current_user dependency
└── main.py
```

---

## Router pattern

Routers validate input and output via Pydantic schemas. No business logic here.

```python
@router.post("/appointments", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    payload: AppointmentIn,
    current_user: User = Depends(get_current_user),
    service: AppointmentService = Depends(),
):
    return await service.create(payload, created_by=current_user.id)
```

---

## Service pattern

Services own business rules: validation, authorization checks, domain events.

```python
class AppointmentService:
    def __init__(self, repo: AppointmentRepository = Depends()):
        self.repo = repo

    async def create(self, payload: AppointmentIn, created_by: UUID) -> Appointment:
        if payload.start >= payload.end:
            raise ValueError("start must be before end")
        return await self.repo.create({**payload.model_dump(), "created_by": created_by})
```

---

## Repository pattern

Repositories contain only database access. No business rules here.

```python
class AppointmentRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def create(self, data: dict) -> Appointment:
        obj = Appointment(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj
```

---

## Configuration

Use `pydantic-settings` with a `.env` file per environment. Never hardcode values.

```python
class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## Error handling

Return structured error responses. Use FastAPI exception handlers for known errors.

```python
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
```

---

## Policies (from domain)

- **Controller → Service → Repository** — no layer skips.
- **Business Logic Only In Services** — routers and repos stay thin.
- **Database Access Only Through Repositories** — no raw SQL outside repos.

---

## References

- `ai/skills/saas/database.md` — schema design and migrations
- `ai/skills/saas/auth.md` — JWT decode and RBAC enforcement
- `ai/skills/saas/frontend.md` — API contract consumed by the frontend
- `ai/domains/saas.md` — domain overview and all policies
