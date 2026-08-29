from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.4.0"
RELEASE_DATE = "2026-08-29"


def main() -> int:
    errors: list[str] = []
    manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("version") != VERSION:
        errors.append("release manifest version does not match")
    if manifest.get("release_date") != RELEASE_DATE:
        errors.append("release manifest date does not match")

    for relative, expected in manifest.get("files", {}).items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"release artefact is missing: {relative}")
            continue
        observed = sha256(path.read_bytes()).hexdigest()
        if observed != expected:
            errors.append(f"release artefact digest differs: {relative}")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != VERSION:
        errors.append("package version does not match")

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    for expected_line in (f"version: {VERSION}", f"date-released: {RELEASE_DATE}"):
        if expected_line not in citation:
            errors.append(f"citation metadata is missing: {expected_line}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## {VERSION} - {RELEASE_DATE}" not in changelog:
        errors.append("changelog release heading does not match")

    errors.extend(_check_local_markdown_links())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Release metadata, links, and artefact hashes verified.")
    return 0


def _check_local_markdown_links() -> list[str]:
    errors: list[str] = []
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in sorted((ROOT / "docs").glob("*.md")) + [ROOT / "README.md"]:
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            if clean_target and not (path.parent / clean_target).resolve().is_file():
                relative = path.relative_to(ROOT)
                errors.append(f"{relative}: missing link target {target}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
