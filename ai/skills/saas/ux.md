# SaaS UX/UI

## When to use this skill

When designing user flows, dashboards, and forms for a SaaS application.

---

## Core principles

- **Most Frequent Operations In Less Than 3 Clicks** — map the top 5 user actions and count clicks.
- **Minimize User Friction** — smart defaults, inline validation, progressive disclosure.
- Accessibility is not optional: WCAG 2.1 AA is the baseline.

---

## Navigation structure

SaaS apps share a common shell layout:

```
┌─────────────────────────────────────────┐
│  Sidebar (nav)  │  Main content area    │
│  Logo           │  Page header          │
│  ─────────────  │  ─────────────────── │
│  Dashboard      │  Page content         │
│  Appointments   │                       │
│  Leads          │                       │
│  Reports        │                       │
│  ─────────────  │                       │
│  Settings       │                       │
│  User / Logout  │                       │
└─────────────────────────────────────────┘
```

- Sidebar shows only items the user's role can access (hide, don't disable).
- Active nav item has a clear visual indicator.
- Mobile: sidebar collapses to a hamburger menu.

---

## Dashboard design

- Lead with summary cards (KPIs): 4 metrics max in the top row.
- Follow with the primary table or calendar view.
- Filters are always visible above the content, not hidden in a modal.
- Show the time range of the data next to every chart or table.

```
┌──────────┬──────────┬──────────┬──────────┐
│ Appts    │ Leads    │ Conv %   │ Util %   │
│  142     │   38     │  26.7%   │  78%     │
│ +12% MTD │  -3 WoW  │ ▲ trend  │ ▼ trend  │
└──────────┴──────────┴──────────┴──────────┘

[ Filter: Date range ▼ ] [ Specialist ▼ ] [ Status ▼ ]

┌────────────────────────────────────────────┐
│  Appointments table                        │
│  ...                                       │
└────────────────────────────────────────────┘
```

---

## Form design

- Group related fields visually (fieldsets or section headers).
- Show required fields clearly (asterisk + legend at the top).
- Validate inline on blur, not only on submit.
- Disable submit button while a request is in flight; show a spinner.
- On success: clear the form and show a toast notification.
- On error: keep form values filled, highlight the error field, show a message near the field.

```tsx
// Example: required field with inline error
<div className="flex flex-col gap-1">
  <label className="text-sm font-medium">Name <span aria-hidden>*</span></label>
  <input
    {...register("name")}
    className={clsx("border rounded px-3 py-2", errors.name && "border-red-500")}
  />
  {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
</div>
```

---

## User flows

### Appointment creation (≤ 3 clicks)

1. Click "New Appointment" (sidebar or page CTA).
2. Fill form (date, time, specialist, lead) → click "Save".
3. Toast confirmation → return to appointment list.

### Lead management (≤ 3 clicks)

1. Click "New Lead" or open existing lead from table.
2. Edit fields inline or in side panel → click "Save".
3. Toast confirmation.

---

## Loading and empty states

- **Loading:** skeleton screens (not spinners) for tables and cards.
- **Empty:** meaningful empty state with a CTA ("No appointments yet — Create one").
- **Error:** inline error message with a "Retry" button; never a blank page.

---

## Responsive design

- Design mobile-first with Tailwind breakpoints (`sm:`, `md:`, `lg:`).
- Tables: on mobile, collapse to card layout or allow horizontal scroll with sticky first column.
- Forms: single column on mobile, two columns on `md:` and above.

---

## Accessibility

- All interactive elements reachable by keyboard (Tab / Enter / Escape).
- Focus ring visible at all times (do not remove `outline`).
- ARIA labels on icon-only buttons.
- Color contrast ratio ≥ 4.5:1 for text.
- Error messages associated with inputs via `aria-describedby`.

---

## Policies (from domain)

- **Most Frequent Operations In Less Than 3 Clicks** — validate before shipping.
- **Minimize User Friction** — smart defaults, inline validation, no unnecessary confirmation dialogs.

---

## References

- `ai/skills/saas/frontend.md` — component and form implementation
- `ai/skills/saas/analytics.md` — KPI card and dashboard data
- `ai/domains/saas.md` — domain overview and all policies
