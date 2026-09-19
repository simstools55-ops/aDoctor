from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    errors = []
    for path in ROOT.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"JSON: {path.relative_to(ROOT)}: {exc}")

    text_suffixes = {".md", ".py", ".json", ".txt", ".gs", ".yml", ".yaml"}
    for path in ROOT.rglob("*"):
        if path.is_file() and (
            path.suffix in text_suffixes
            or path.name in {"README.md", "VERSION", "CHANGELOG.md"}
        ):
            try:
                path.read_text(encoding="utf-8")
            except Exception as exc:
                errors.append(f"UTF8: {path.relative_to(ROOT)}: {exc}")

    for path in ROOT.rglob("*"):
        if (
            path.name in {"__pycache__", ".pytest_cache", ".DS_Store", "Thumbs.db"}
            or path.suffix in {".pyc", ".pyo"}
        ):
            errors.append(f"TRANSIENT: {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors))
        return 1
    print("release audit passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
