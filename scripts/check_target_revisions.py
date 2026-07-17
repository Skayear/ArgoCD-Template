#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
CLIENTS_DIR = REPO_ROOT / "clients"
EXPECTED_TARGET_REVISION = "main"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML content must be a mapping")
    return data


def get_target_revision(data: dict) -> str | None:
    return (
        data.get("config", {})
        .get("spec", {})
        .get("source", {})
        .get("targetRevision")
    )


def get_override(data: dict) -> tuple[bool, str | None]:
    ci = data.get("ci", {})
    allow = bool(ci.get("allowNonMainTargetRevision", False))
    reason = ci.get("allowNonMainTargetRevisionReason")
    return allow, reason


def main() -> int:
    value_files = sorted(CLIENTS_DIR.rglob("values.yaml"))
    failures: list[str] = []
    warnings: list[str] = []

    if not value_files:
        print("No client values files found under clients/**/values.yaml")
        return 1

    for path in value_files:
        rel_path = path.relative_to(REPO_ROOT)
        try:
            data = load_yaml(path)
        except Exception as exc:  # pragma: no cover - CI-oriented guard
            failures.append(f"{rel_path}: could not parse YAML: {exc}")
            continue

        target_revision = get_target_revision(data)
        allow_override, override_reason = get_override(data)

        if not target_revision:
            failures.append(
                f"{rel_path}: missing config.spec.source.targetRevision"
            )
            continue

        if target_revision == EXPECTED_TARGET_REVISION:
            continue

        if allow_override:
            reason_suffix = (
                f" (reason: {override_reason})" if override_reason else ""
            )
            warnings.append(
                f"{rel_path}: targetRevision={target_revision!r} allowed by ci.allowNonMainTargetRevision{reason_suffix}"
            )
            continue

        failures.append(
            f"{rel_path}: targetRevision={target_revision!r}, expected {EXPECTED_TARGET_REVISION!r}"
        )

    for warning in warnings:
        print(f"WARNING: {warning}")

    if failures:
        print("ERROR: targetRevision validation failed.")
        for failure in failures:
            print(f" - {failure}")
        print()
        print(
            "If a non-main targetRevision is really intentional, add this explicit override to the client values file:"
        )
        print()
        print("ci:")
        print("  allowNonMainTargetRevision: true")
        print('  allowNonMainTargetRevisionReason: "temporary branch test"')
        return 1

    print("targetRevision validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
