#!/usr/bin/env python3
"""Collect policy markdown files and emit a merged JSON payload.

Output format:
{
  "filelist": ["/abs/path/a.md", ...],
  "policy_merge": "...merged markdown text..."
}
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

N8N_REPO_ROOT = Path("/home/node/.n8n-files/argocd")


def detect_base_dir(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    if N8N_REPO_ROOT.exists():
        return N8N_REPO_ROOT
    # local fallback: repo root where .agent exists
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent.parent


def policy_candidates(base_dir: Path) -> list[Path]:
    cwd = Path.cwd()
    return [
        cwd / "merge_policy_exclusion.json",
        cwd / "merge_policy_exclude.json",
        base_dir / ".agent" / "merge_policy_exclusion.json",
        base_dir / ".agent" / "merge_policy_exclude.json",
        N8N_REPO_ROOT / ".agent" / "merge_policy_exclusion.json",
        N8N_REPO_ROOT / ".agent" / "merge_policy_exclude.json",
    ]


def load_policy(base_dir: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "excludeContains": [".git/"],
        "excludeGlobs": [],
        "excludeFileNames": [],
        "excludeExtensions": [],
    }

    for candidate in policy_candidates(base_dir):
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            data = parse_loose_policy(candidate.read_text(encoding="utf-8"))
            if not data:
                continue

        for key in defaults:
            value = data.get(key, defaults[key])
            if isinstance(value, list):
                defaults[key] = [str(v) for v in value]
        return defaults

    return defaults


def parse_loose_policy(raw: str) -> dict[str, list[str]]:
    """Best-effort parser for near-JSON policy files."""
    keys = (
        "excludeContains",
        "excludeGlobs",
        "excludeFileNames",
        "excludeExtensions",
    )
    parsed: dict[str, list[str]] = {}

    for key in keys:
        match = re.search(rf'"{key}"\s*:\s*\[(.*?)\]', raw, flags=re.DOTALL)
        if not match:
            continue
        body = match.group(1)
        items: list[str] = []
        for part in body.split(","):
            token = part.strip()
            if not token:
                continue
            token = token.strip("'\"")
            if token:
                items.append(token)
        parsed[key] = items

    return parsed


def should_exclude(path: Path, base_dir: Path, policy: dict[str, Any]) -> bool:
    rel = path.relative_to(base_dir).as_posix()
    name = path.name

    for needle in policy.get("excludeContains", []):
        if needle and needle in rel:
            return True

    for pattern in policy.get("excludeGlobs", []):
        if pattern and path.match(pattern):
            return True
        if pattern and Path(rel).match(pattern):
            return True

    if name in set(policy.get("excludeFileNames", [])):
        return True

    ext = path.suffix
    if ext in set(policy.get("excludeExtensions", [])):
        return True

    return False


def collect_markdown_files(base_dir: Path, policy: dict[str, Any]) -> list[Path]:
    files: list[Path] = []
    for path in base_dir.rglob("*.md"):
        if not path.is_file():
            continue
        if should_exclude(path, base_dir, policy):
            continue
        files.append(path.resolve())
    files.sort(key=lambda p: str(p))
    return files


def collect_excluded_markdown_files(base_dir: Path, policy: dict[str, Any]) -> list[Path]:
    files: list[Path] = []
    for path in base_dir.rglob("*.md"):
        if not path.is_file():
            continue
        if not should_exclude(path, base_dir, policy):
            continue
        files.append(path.resolve())
    files.sort(key=lambda p: str(p))
    return files


def merge_files(files: list[Path]) -> str:
    chunks: list[str] = []
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        header = f"\n\n# FILE: {file_path}\n\n"
        chunks.append(header + content)
    return "".join(chunks).lstrip()


def build_payload(base_dir_value: str | None = None) -> dict[str, Any]:
    base_dir = detect_base_dir(base_dir_value)
    policy = load_policy(base_dir)
    files = collect_markdown_files(base_dir, policy)
    return {
        "filelist": [str(path) for path in files],
        "policy_merge": merge_files(files),
    }


def build_policy_file_list(base_dir_value: str | None = None) -> list[str]:
    base_dir = detect_base_dir(base_dir_value)
    policy = load_policy(base_dir)
    files = collect_markdown_files(base_dir, policy)
    output: list[str] = []
    for path in files:
        rel = path.relative_to(base_dir).as_posix()
        output.append(f"/{rel}")
    return output


def build_policy_excluded_file_list(base_dir_value: str | None = None) -> list[str]:
    base_dir = detect_base_dir(base_dir_value)
    policy = load_policy(base_dir)
    files = collect_excluded_markdown_files(base_dir, policy)
    output: list[str] = []
    for path in files:
        rel = path.relative_to(base_dir).as_posix()
        output.append(f"/{rel}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and merge markdown policies")
    parser.add_argument("--base-dir", default=None, help="Repo root to scan")
    parser.add_argument("--output", default=None, help="Optional output JSON file")
    args = parser.parse_args()

    payload = build_payload(args.base_dir)

    body = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body + "\n", encoding="utf-8")
    else:
        print(body)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
