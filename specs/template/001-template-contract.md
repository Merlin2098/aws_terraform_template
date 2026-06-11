# Template contract

## Context

This spec defines what the AWS + Terraform + Python template provides to a
host repository, what it expects from the host environment, and what it
intentionally does not provide. It is the contract between the template
and any project bootstrapped from it.

## Contract

### What the template provides

- **`infra/`** — Terraform baseline (S3 artifacts bucket, Glue execution
  IAM role, standard tags). See [`002-infra-baseline.md`](002-infra-baseline.md).
- **`src/`** — Python package skeleton with `config/`, `contracts/`,
  `jobs/`, `transformations/` subfolders for ETL workloads.
- **`scripts/`** — Operational entrypoints (packaging, testing, treemap,
  Windows wrappers). All invoked via the `Makefile`.
- **`ai/`** — AI guidance layer (`skills/`, `skills.yaml`, `context.yaml`,
  `installer.py`, runtime loaders). Read-only in host repos.
- **`specs/template/`** — Inherited contracts (this folder). Read-only in
  host repos.
- **`docs/`** — Human-authored reference (`terra_principles.md`, Terraform
  cheatsheet, Windows setup).
- **Capability-driven dependencies** — descriptors map active capabilities to
  `pyproject.toml` extras and dependency groups.
- **Capability catalog** — every available capability is recorded in
  `.template-profile.yaml` with an explicit enabled state.
- **Installer** — `ai/installer.py` copies the template into a host repo
  with repeatable `--enable category:name`, the `--saas` shortcut, and
  structure flags. An empty interactive selection enables all capabilities;
  `none` explicitly enables none.

### What the template expects from the host

- Python `>= 3.x` matching `pyproject.toml`.
- When Terraform or AWS capabilities are enabled: Terraform `>= 1.10`, AWS
  provider `>= 5.81`, and AWS credentials provided out-of-band.
- `uv` available.
- A POSIX shell or PowerShell with the documented Windows wrappers.

### What the template does not provide

- CI/CD pipelines (GitHub Actions, etc.). The host wires its own.
- Secrets management. Use AWS Secrets Manager or environment variables;
  never commit secrets.
- Production-grade defaults. Defaults favor `destroyability`, `low-cost
  dev`, and `reproducibility` per [`docs/terra_principles.md`](../../docs/terra_principles.md).
- Host-specific runbooks. Hosts author their own under `docs/runbooks/`
  (or equivalent) when operational complexity grows.
- Remote backend wiring. The template ships
  [`infra/backend.tf.example`](../../infra/backend.tf.example); the host
  renames it to `backend.tf` (gitignored) when ready.

## Invariants

- The template is installed, not cloned: the host receives a copy filtered
  by `ai/installer.py` (cloud/local, with/without structure).
- `ai/` and `specs/template/` are read-only in the host (gitignored via
  the installer's `HOST_EXTRA_GITIGNORE_ENTRIES`).
- Re-running the installer refreshes inherited folders without touching
  host-authored content (`specs/project/`, `src/jobs/`, etc.).
- Standard tags `Project`, `Environment`, `Owner`, `ManagedBy=Terraform`
  are applied to every Terraform-managed AWS resource (see
  [`infra/main.tf`](../../infra/main.tf)).

## Out of scope

- The internal evolution of the template itself (template-development
  workflow). That lives in [`AGENTS.md`](../../AGENTS.md) and
  [`docs/`](../../docs/).
- Multi-environment Terraform layouts (dev/staging/prod). The template
  ships a single-environment baseline; multi-env is a host concern.

## References

- [`AGENTS.md`](../../AGENTS.md)
- [`ai/installer.py`](../../ai/installer.py)
- [`docs/terra_principles.md`](../../docs/terra_principles.md)
- [`002-infra-baseline.md`](002-infra-baseline.md)
- [`003-ai-guidance-layers.md`](003-ai-guidance-layers.md)
