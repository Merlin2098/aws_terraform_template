# SaaS Frontend

## When to use this skill

When building UI for a SaaS application with React, Vite, and Tailwind CSS.
For AWS-deployed SPAs (S3 + CloudFront), also consult `ai/skills/frontend/react_vite_aws.md`.

---

## Stack

| Layer | Technology |
|---|---|
| Framework | React 18 |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Routing | React Router v6 |
| HTTP client | Axios (see `ai/skills/saas/backend.md` for the contract) |
| Forms | React Hook Form + Zod |

---

## Project structure

```
src/
├── components/     # reusable UI components (no business logic)
├── pages/          # route-level components (compose components)
├── hooks/          # custom hooks (data fetching, state, side effects)
├── services/       # API call functions (axios wrappers)
├── lib/            # shared utilities, formatters, constants
└── types/          # TypeScript interfaces / Zod schemas
```

---

## Component design

- Design components to be reusable before writing page-level code.
- A component owns its local UI state only. Business logic belongs in hooks.
- Props must be typed (TypeScript interfaces or Zod-inferred types).
- Prefer composition over configuration for variant components.

```tsx
// good — composition
<Card>
  <Card.Header>Title</Card.Header>
  <Card.Body>Content</Card.Body>
</Card>

// avoid — prop explosion
<Card title="Title" body="Content" headerVariant="large" ... />
```

---

## Data fetching

Use a custom hook per resource. Keep fetching logic out of components.

```tsx
// hooks/useAppointments.ts
export function useAppointments(filters: AppointmentFilters) {
  const [data, setData] = useState<Appointment[]>([]);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error' | 'success'>('idle');

  useEffect(() => {
    setStatus('loading');
    appointmentService.list(filters)
      .then(res => { setData(res); setStatus('success'); })
      .catch(() => setStatus('error'));
  }, [filters]);

  return { data, status };
}
```

Three-state pattern: `idle | loading | error | success` — never a boolean `isLoading`.

---

## Forms

- Use React Hook Form for all forms; avoid uncontrolled inputs.
- Validate with Zod schemas; share the schema with the backend contract.
- Show inline validation errors immediately on blur, not only on submit.

```tsx
const schema = z.object({
  name: z.string().min(1, 'Required'),
  email: z.string().email('Invalid email'),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema),
});
```

---

## Routing

- Use `<Outlet>` for nested layouts (dashboard shell, auth shell).
- Protect routes with a wrapper that checks auth state before rendering.
- Use `useNavigate` for programmatic navigation after mutations.

---

## Policies (from domain)

- **Component First** — build the component before the page.
- **No Business Logic Inside UI Components** — move it to a hook.
- **API Driven UI** — all data comes from API services; no direct DB access.

---

## References

- `ai/skills/saas/backend.md` — API contract and service layer
- `ai/skills/frontend/api_client_patterns.md` — axios client setup
- `ai/skills/saas/ux.md` — UX patterns for SaaS dashboards
- `ai/domains/saas.md` — domain overview and all policies
