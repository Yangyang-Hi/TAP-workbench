#!/usr/bin/env python3
"""Generate the versioned reported-reason dictionary from the supplied mapping Markdown."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROW = re.compile(
    r"\|\s*(\d+)\s*\|\s*`(.*?)`\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$"
)


def normalize(label: str) -> str:
    # Only whitespace directly surrounding the hierarchy separator is normalized.
    return " - ".join(part.strip() for part in re.split(r"\s+-\s+", label))


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate_reported_reason_mapping.py INPUT.md OUTPUT.json")
    source, target = map(Path, sys.argv[1:])
    entries: list[dict[str, str]] = []
    keys: dict[str, str] = {}
    for line in source.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if not match:
            continue
        original = match.group(2)
        key = normalize(original)
        if key in keys and keys[key] != original:
            raise SystemExit(f"normalized label collision: {keys[key]!r} vs {original!r}")
        keys[key] = original
        entries.append(
            {
                "original_label": original,
                "display_name_en": match.group(3),
                "description": match.group(4),
                "mapping_status": "pending_confirmation" if match.group(5) == "待确认" else "draft",
            }
        )
    if len(entries) != 126:
        raise SystemExit(f"expected 126 mapping rows, got {len(entries)}")
    payload = {
        "version": "2026-10-26.v1",
        "normalization": "trim whitespace around hierarchy separators only",
        "entries": entries,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
