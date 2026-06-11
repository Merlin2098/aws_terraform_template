# Linux Setup

This guide prepares an Ubuntu-like Linux machine to use this template and to
install it into another repository.

Use this Linux documentation set in this order:

1. `README.md` for the general operational flow
2. [uv_install.md](uv_install.md) for uv installation and manual/corporate usage
3. [make_cheatlist.md](make_cheatlist.md) for day-to-day `make` command examples

## Prepare the Template Repository

From the repository root:

```bash
./scripts/linux/setup_env.sh
```

This Linux wrapper resolves Python automatically, validates `uv`, and delegates
the environment sync to `scripts/run_uv_sync.py`.

By default, the local uv workflow installs:

- the shared base dependencies from `pyproject.toml`
- the `dev-local` dependency group

The cloud uv workflow installs:

- the shared base dependencies from `pyproject.toml`
- the `local` and `cloud` optional dependency sets
- the `dev-local` and `dev-cloud` dependency groups

Install pre-commit into the current repository environment:

```bash
./.venv/bin/pre-commit install
./.venv/bin/pre-commit --version
```

To run all configured hooks manually:

```bash
./.venv/bin/pre-commit run --all-files
```

## Refresh or Change the Environment

To refresh the local uv environment after editing dependencies:

```bash
./scripts/linux/update_venv.sh
```

To prepare the local environment with cloud dependencies explicitly:

```bash
./scripts/linux/update_venv.sh --profile cloud
```

For uv-based hosts, the default profile comes from `.template-profile`. A local
host stays on `base + dev-local` unless you override it explicitly, and
a cloud host defaults to `base + local + cloud + dev-local + dev-cloud`.

To sync only runtime dependencies:

```bash
./scripts/linux/setup_env.sh --no-dev
./scripts/linux/update_venv.sh --no-dev
```

## Use Make On Linux

On Ubuntu and similar distributions, native `make` is the standard path:

```bash
make test
make uv-init
make uv-update
```

See [make_cheatlist.md](make_cheatlist.md) for ready-to-copy examples.

## uv Installation and Validation

For uv installation paths, manual/corporate workflows, and validation guidance,
see [uv_install.md](uv_install.md).

## Install This Template Into Another Repo

Preview the install without writing files:

```bash
python3 install_linux.py --dry-run --target /path/to/target-repo
```

Install the template with an explicit target path:

```bash
python3 install_linux.py --target /path/to/target-repo
```

Install and choose the dependency profile non-interactively:

```bash
python3 install_linux.py --target /path/to/target-repo --local
python3 install_linux.py --target /path/to/target-repo --cloud
```

Overwrite existing target files only when intentional:

```bash
python3 install_linux.py --target /path/to/target-repo --force
```

`install_linux.py` copies the template into a host repository. It does not
bootstrap the current repository environment; use `./scripts/linux/setup_env.sh`
for that.
