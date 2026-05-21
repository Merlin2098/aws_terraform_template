#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

python_path=""
profile=""
use_dev_dependencies="true"
dev_option=""

write_step() {
    printf '%s\n' "$1"
}

write_phase() {
    printf '\n=== %s ===\n' "$1"
}

usage() {
    cat <<'EOF'
Usage: ./scripts/linux/setup_env.sh [options]

Options:
  --python-path PATH  Use this Python interpreter explicitly.
  --profile PROFILE   Use the local or cloud dependency profile.
  --include-dev       Install dev dependency groups explicitly.
  --no-dev            Skip dev dependency groups.
  -h, --help          Show this help text.
EOF
}

test_command() {
    local command="$1"
    shift
    "${command}" "$@" --version >/dev/null 2>&1
}

resolve_python_command() {
    if [[ -n "${python_path}" ]]; then
        if [[ ! -x "${python_path}" ]]; then
            printf "Python not found at '%s'.\n" "${python_path}" >&2
            exit 1
        fi
        if ! test_command "${python_path}"; then
            printf "Python at '%s' did not respond correctly.\n" "${python_path}" >&2
            exit 1
        fi
        printf '%s\n' "${python_path}"
        return
    fi

    local candidates=("python3" "python")
    local candidate=""
    for candidate in "${candidates[@]}"; do
        if command -v "${candidate}" >/dev/null 2>&1 && test_command "${candidate}"; then
            printf '%s\n' "${candidate}"
            return
        fi
    done

    printf "Unable to resolve a working Python interpreter. Tried: python3, python.\n" >&2
    exit 1
}

validate_profile() {
    local selected="$1"
    if [[ -z "${selected}" ]]; then
        return
    fi
    if [[ "${selected}" != "local" && "${selected}" != "cloud" ]]; then
        printf "Profile must be 'local' or 'cloud'.\n" >&2
        exit 1
    fi
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --python-path)
                if [[ $# -lt 2 ]]; then
                    printf "Expected a value after --python-path.\n" >&2
                    exit 1
                fi
                python_path="$2"
                shift 2
                ;;
            --profile)
                if [[ $# -lt 2 ]]; then
                    printf "Expected a value after --profile.\n" >&2
                    exit 1
                fi
                profile="$2"
                shift 2
                ;;
            --include-dev)
                if [[ "${dev_option}" == "no-dev" ]]; then
                    printf "Use either --include-dev or --no-dev, but not both.\n" >&2
                    exit 1
                fi
                use_dev_dependencies="true"
                dev_option="include-dev"
                shift
                ;;
            --no-dev)
                if [[ "${dev_option}" == "include-dev" ]]; then
                    printf "Use either --include-dev or --no-dev, but not both.\n" >&2
                    exit 1
                fi
                use_dev_dependencies="false"
                dev_option="no-dev"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                printf "Unknown argument: %s\n" "$1" >&2
                usage >&2
                exit 1
                ;;
        esac
    done
}

parse_args "$@"
validate_profile "${profile}"

selected_python="$(resolve_python_command)"

write_step "Starting uv environment setup for this repository."

write_phase "Phase 1: Resolve Python"
write_step "[Python] Using interpreter: ${selected_python}"
"${selected_python}" --version

write_phase "Phase 2: Validate Tooling"
if "${selected_python}" -m uv --version >/dev/null 2>&1; then
    write_step "[uv] Using uv via ${selected_python} -m uv"
elif command -v uv >/dev/null 2>&1 && uv --version >/dev/null 2>&1; then
    write_step "[uv] Using uv from PATH"
else
    printf "Unable to resolve uv. Install uv for the selected Python interpreter or expose uv in PATH.\n" >&2
    exit 1
fi

if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
    printf "pyproject.toml is required for the uv setup flow.\n" >&2
    exit 1
fi
write_step "[Project] Verified pyproject.toml."

write_phase "Phase 3: Sync Environment"
command=("${selected_python}" "${REPO_ROOT}/scripts/run_uv_sync.py" "init" "--python-path" "${selected_python}")
if [[ -n "${profile}" ]]; then
    command+=("--profile" "${profile}")
fi
if [[ "${use_dev_dependencies}" == "false" ]]; then
    command+=("--no-dev")
fi
write_step "[Dependencies] Running: ${command[*]}"
(
    cd "${REPO_ROOT}"
    "${command[@]}"
)

write_phase "Phase 4: Summary"
write_step "Environment setup completed successfully."
printf 'Suggested interpreter path: %s\n' "${REPO_ROOT}/.venv/bin/python"
