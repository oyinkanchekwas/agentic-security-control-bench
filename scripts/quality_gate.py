from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".venv", "__pycache__", "build", "dist"}
TEXT_SUFFIXES = {"", ".cff", ".json", ".jsonl", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
ALLOW_SPELLING_RULE_FILES = {"scripts/quality_gate.py"}

US_SPELLINGS = {
    "behavior": "behaviour",
    "artifact": "artefact",
    "normalize": "normalise",
    "normalized": "normalised",
    "summarize": "summarise",
    "analyze": "analyse",
    "analyzer": "analyser",
    "optimization": "optimisation",
    "prioritize": "prioritise",
    "specialized": "specialised",
    "deserialization": "deserialisation",
    "parameterized": "parameterised",
}

REALISTIC_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def main() -> int:
    errors: list[str] = []
    for path in iter_text_files():
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        if relative not in ALLOW_SPELLING_RULE_FILES:
            for bad, good in US_SPELLINGS.items():
                if re.search(rf"(?<![a-z]){re.escape(bad)}", lower):
                    errors.append(f"{relative}: use British English: {bad!r} -> {good!r}")
        if "\u2014" in text:
            errors.append(f"{relative}: em dash found")
        for pattern in REALISTIC_SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{relative}: realistic secret-shaped text found")
    if errors:
        sys.stderr.write("\n".join(errors) + "\n")
        return 1
    print("Quality gate passed.")
    return 0


def iter_text_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        if any(part in SKIP_PARTS or part.endswith(".egg-info") for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES:
            paths.append(path)
    return sorted(paths)


if __name__ == "__main__":
    raise SystemExit(main())
