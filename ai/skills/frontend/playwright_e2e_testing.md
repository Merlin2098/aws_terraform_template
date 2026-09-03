# Playwright E2E Testing Patterns

## When to use

- Writing a new `*.spec.ts` file for a Playwright test suite
- Debugging why a spec shows an empty snapshot/timeline panel in Playwright
  UI Mode (`playwright test --ui`)
- Investigating flaky/intermittent failures in an E2E suite, especially the
  first run after the dev server has been idle

## Core idea

Playwright UI Mode renders one timeline per **executed test**, not per file
or per group. A test tree node that represents a container — not an actual
test run — has no timeline to show. The most common cause of that is
`test.describe(...)`: it is convenient for grouping in code, but it also
turns the top-level tree node into a collapsed container. Selecting that
container node directly (instead of expanding it and picking an individual
`test()` inside) leaves the Actions/snapshot panel empty, even when every
test inside passed.

---

## Flat test structure (required for UI Mode snapshots to render)

Declare tests with `test()` at the top level of the file. Use a shared
string prefix in each test name instead of `test.describe(...)` if you want
visual grouping in the UI Mode tree:

```ts
import { test, expect } from "@playwright/test";

test("checkout: shows both payment method options", async ({ page }) => {
  // ...
});

test("checkout: 'card' opens the card payment form", async ({ page }) => {
  // ...
});
```

Avoid:

```ts
// Groups visually in code, but the describe node itself has no timeline —
// selecting it directly in UI Mode shows an empty panel.
test.describe("checkout: payment method selector", () => {
  test("shows both payment method options", async ({ page }) => { /* ... */ });
});
```

If a suite already uses `describe` and the panel is empty, the fix is either
to flatten it, or to make sure you always select the individual `test()`
row (with its own pass/fail icon) rather than the collapsed parent row.

---

## Diagnosing an empty snapshot panel

1. Check for `test.describe(...)` first — it's the most common cause (see
   above).
2. If the file has no `describe`, confirm the test actually produces a
   trace: run it from the command line with `--trace=on` and check that
   `test-results/<test-name>/trace.zip` exists and is non-trivial (unzip it
   and confirm `resources/` contains `.png` snapshot files, or open it with
   `npx playwright show-trace <file>.zip`). If the CLI trace is complete but
   UI Mode still shows nothing, fully restart UI Mode (stop the process, not
   just re-run inside the same session) — a spec file created or edited
   while UI Mode was already running sometimes isn't re-indexed with tracing
   until the session restarts.
3. Only after ruling out both of the above, suspect a config issue
   (`trace`/`screenshot` options in the Playwright config).

---

## Auth setup pattern (`*.setup.ts` + storageState)

For suites that need an authenticated session, use a dedicated setup
project instead of logging in inside every spec:

```ts
// tests/e2e/auth.setup.ts
import { test as setup, expect } from "@playwright/test";

const authFile = "tests/e2e/.auth/user.json";

setup("authenticate", async ({ page }) => {
  const email = process.env.E2E_USER_EMAIL;
  const password = process.env.E2E_USER_PASSWORD;
  if (!email || !password) {
    throw new Error("E2E_USER_EMAIL and E2E_USER_PASSWORD must be set to run e2e tests.");
  }
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).not.toHaveURL(/\/login/);
  await page.context().storageState({ path: authFile });
});
```

```ts
// playwright.config.ts
projects: [
  { name: "setup", testMatch: /.*\.setup\.ts/ },
  {
    name: "chromium",
    use: { ...devices["Desktop Chrome"], storageState: "tests/e2e/.auth/user.json" },
    dependencies: ["setup"],
  },
],
```

Fail loudly (throw) if the required env vars are missing — don't silently
fall back to a default user, which hides misconfiguration as a test
failure with a confusing error later.

---

## Cold-start false negatives

`webServer.reuseExistingServer` (typically `!process.env.CI`) reuses an
already-running dev server, or boots one and waits for it to respond. A dev
server using an on-demand compiler (Next.js Turbopack, Vite in dev mode)
can take longer than the default navigation timeout to serve a route it
hasn't compiled yet — especially with multiple parallel workers all hitting
it right as it comes up.

If the **first** run after a period of inactivity times out on `page.goto`
(including the auth setup test itself), don't assume the test or app is
broken — retry once (the server is warm now) or run that first pass with
`--workers=1`. Only treat it as a real failure if it still fails against an
already-warm server.

---

## Prefer semantic role selectors

```ts
page.getByRole("button", { name: /Create/i })
page.getByRole("menuitem", { name: "Option A" })
page.getByRole("heading", { name: "Page Title" })
```

For a portal-rendered dropdown/menu (Radix UI, shadcn/ui, and similar), the
open menu item exposes an accessible `menuitem` role — use that instead of a
raw text or CSS selector once the trigger has been clicked.

---

## Avoid

- Wrapping tests in `test.describe(...)` when the suite is driven primarily
  through UI Mode — it silently breaks the snapshot panel for that group.
- Re-implementing login inside individual specs instead of a shared
  `*.setup.ts` + `storageState` project dependency.
- Treating a cold-start timeout on the first run as a genuine test failure
  without retrying against a warm server first.
- Committing `playwright-report/` or `test-results/` — clean them up
  (`rm -rf playwright-report test-results`) after local debugging runs.

## See also

- `ai/skills/frontend/api_client_patterns.md` — shared client patterns that
  E2E specs often exercise indirectly through the UI.
