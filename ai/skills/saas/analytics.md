# SaaS Analytics

## When to use this skill

When designing operational dashboards or KPI tracking for a SaaS application.
This covers business metrics visible to OWNER/ADMIN users, not data warehouse analytics.

---

## Scope

| In scope | Out of scope |
|---|---|
| Operational KPIs (real-time counts, rates) | Data warehouse / OLAP queries |
| Dashboard filters and aggregations | Machine learning or predictive analytics |
| Business metrics (leads, appointments) | AWS Athena / Glue (see `ai/skills/data/`) |
| Historical snapshots | Complex event processing |

---

## Base metrics

These metrics must be tracked from day one of the SaaS schema design:

| Metric | Description |
|---|---|
| Appointments | Total scheduled, confirmed, cancelled, completed |
| Leads | Total active, converted, lost |
| Conversion rate | Leads → confirmed appointments |
| Cancellation rate | Cancelled / total appointments |
| Overbooking | Appointments exceeding capacity slots |
| Utilization | Confirmed appointments / available slots |

---

## Data modeling for analytics

Define analytics requirements before finalizing the schema.

```sql
-- Snapshot table for daily aggregates (do not compute from live data alone)
CREATE TABLE appointment_daily_snapshots (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL,
    specialist_id UUID REFERENCES user_profiles(id),
    total         INT NOT NULL DEFAULT 0,
    confirmed     INT NOT NULL DEFAULT 0,
    cancelled     INT NOT NULL DEFAULT 0,
    completed     INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (snapshot_date, specialist_id)
);
```

Populate snapshots via a scheduled job (e.g. nightly cron via Railway or GitHub Actions), not on every request.

---

## API design for dashboards

Return aggregated data from dedicated endpoints, not from filtering live tables.

```python
# api/v1/endpoints/analytics.py
@router.get("/analytics/appointments/summary")
async def appointment_summary(
    start_date: date,
    end_date: date,
    specialist_id: UUID | None = None,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(),
) -> AppointmentSummaryOut:
    require_role(current_user, ["OWNER", "ADMIN"])
    return await service.appointment_summary(start_date, end_date, specialist_id)
```

---

## Frontend dashboard patterns

- Always provide date-range filters (default: last 30 days).
- Show trend vs. prior period (e.g. +12% vs last month).
- Use skeleton loaders while data is fetching; never show empty charts.
- Refresh dashboard data every 5 minutes without full page reload.

```tsx
// hooks/useAppointmentSummary.ts
export function useAppointmentSummary(range: DateRange) {
  const [data, setData] = useState<AppointmentSummary | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error' | 'success'>('idle');

  useEffect(() => {
    const load = () => {
      setStatus('loading');
      analyticsService.appointmentSummary(range)
        .then(d => { setData(d); setStatus('success'); })
        .catch(() => setStatus('error'));
    };
    load();
    const interval = setInterval(load, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [range]);

  return { data, status };
}
```

---

## Filters and aggregations

Always allow filtering by:
- Date range (start, end)
- Specialist
- Status

Aggregate on the server, not on the client. Return pre-computed totals in the API response.

---

## Policies (from domain)

- **Analytics Requirements Must Be Defined During Data Modeling** — add metrics columns at schema design time; retrofitting is expensive.
- **Historical Tracking Required** — use snapshot tables; computing history from live data is slow and unreliable.

---

## References

- `ai/skills/saas/database.md` — snapshot table design and audit fields
- `ai/skills/saas/backend.md` — AnalyticsService and repository pattern
- `ai/skills/saas/frontend.md` — dashboard component and hook patterns
- `ai/skills/saas/ux.md` — dashboard layout and filter UX
- `ai/domains/saas.md` — domain overview and all policies
