import hashlib
import subprocess
import sys
from pathlib import Path

REQ_FILES = (Path("requirements.local.txt"), Path("requirements.dev.txt"))
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


def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def requirements_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.md5()
    for requirement_path in paths:
        if not requirement_path.exists():
            continue
        digest.update(str(requirement_path.resolve()).encode("utf-8"))
        digest.update(requirement_path.read_bytes())
    return digest.hexdigest()


def main():
    existing_req_files = tuple(path for path in REQ_FILES if path.exists())
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
    subprocess.run(
        [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.local.txt",
            "-r",
            "requirements.dev.txt",
        ],
        check=True,
    )

    HASH_FILE.write_text(current_hash)
    print("Dependencies updated.")


if __name__ == "__main__":
    main()
