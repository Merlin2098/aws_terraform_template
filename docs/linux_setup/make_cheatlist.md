# Linux Make Cheatlist

Use these commands from the repository root on Ubuntu and similar
distributions.

## Common Targets

```bash
make treemap
make test
make package
make ai-refresh
```

## uv Environment Targets

```bash
make uv-init
make uv-update
make uv-reset
```

## Direct Wrapper Commands

```bash
./scripts/linux/setup_env.sh
./scripts/linux/setup_env.sh --profile cloud
./scripts/linux/update_venv.sh
./scripts/linux/update_venv.sh --no-dev
```
