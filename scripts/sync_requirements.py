import hashlib
import subprocess
from pathlib import Path

REQ_FILE = Path("requirements.txt")
HASH_FILE = Path(".venv/.req_hash")

def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()

def main():
    if not REQ_FILE.exists():
        return

    current_hash = file_hash(REQ_FILE)

    if HASH_FILE.exists():
        stored_hash = HASH_FILE.read_text()
        if stored_hash == current_hash:
            print("Requirements unchanged. Skipping install.")
            return

    print("Installing dependencies...")
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)

    HASH_FILE.write_text(current_hash)
    print("Dependencies updated.")

if __name__ == "__main__":
    main()