import hashlib
import subprocess
import sys
from pathlib import Path

REQUIREMENTS_GLOB = "requirements*.txt"
HASH_FILE = Path(".venv/.req_hash")


def venv_python() -> Path:
    candidates = (
        Path(".venv/Scripts/python.exe"),
        Path(".venv/bin/python"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def requirement_files() -> tuple[Path, ...]:
    files = sorted(
        (
            path
            for path in Path(".").glob(REQUIREMENTS_GLOB)
            if path.is_file() and path.parent == Path(".")
        ),
        key=lambda path: path.name.lower(),
    )
    return tuple(files)


def requirements_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.md5()
    for requirement_path in paths:
        if not requirement_path.exists():
            continue
        digest.update(str(requirement_path.resolve()).encode("utf-8"))
        digest.update(requirement_path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    existing_req_files = requirement_files()
    if not existing_req_files:
        return

    current_hash = requirements_hash(existing_req_files)
    python_executable = venv_python()

    if HASH_FILE.exists():
        stored_hash = HASH_FILE.read_text()
        if stored_hash == current_hash:
            print("Requirements unchanged. Skipping install.")
            return

    print("Installing dependencies...")
    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    install_command = [str(python_executable), "-m", "pip", "install"]
    for requirement_file in existing_req_files:
        install_command.extend(["-r", requirement_file.as_posix()])

    subprocess.run(
        install_command,
        check=True,
    )

    HASH_FILE.write_text(current_hash)
    print("Dependencies updated.")


if __name__ == "__main__":
    main()
