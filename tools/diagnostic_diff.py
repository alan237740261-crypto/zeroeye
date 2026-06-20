#!/usr/bin/env python3
"""
Diagnostic metadata diff tool for Tent of Trials platform.

Compares two diagnostic metadata JSON files (build-XXX.json) and prints
a human-readable diff. Useful for reviewers to understand what changed
between submissions.

Usage:
    python3 tools/diagnostic_diff.py old.json new.json
    python3 tools/diagnostic_diff.py old.json new.json --json
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional


def load_diagnostic(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Cannot load {path}: {e}", file=sys.stderr)
        return None


def compare_module_dicts(
    old_modules: List[Dict[str, Any]],
    new_modules: List[Dict[str, Any]],
) -> Dict[str, Any]:
    old_by_name = {m["name"]: m for m in old_modules}
    new_by_name = {m["name"]: m for m in new_modules}

    old_names = set(old_by_name.keys())
    new_names = set(new_by_name.keys())

    added = sorted(new_names - old_names)
    removed = sorted(old_names - new_names)
    common = sorted(old_names & new_names)

    changed = []
    for name in common:
        old_m = old_by_name[name]
        new_m = new_by_name[name]
        changes = {}
        if old_m.get("status") != new_m.get("status"):
            changes["status"] = {"from": old_m.get("status"), "to": new_m.get("status")}
        if old_m.get("artifact") != new_m.get("artifact"):
            changes["artifact"] = {"from": old_m.get("artifact"), "to": new_m.get("artifact")}
        if old_m.get("elapsed_seconds") != new_m.get("elapsed_seconds"):
            changes["elapsed_seconds"] = {
                "from": old_m.get("elapsed_seconds"),
                "to": new_m.get("elapsed_seconds"),
                "delta": (new_m.get("elapsed_seconds") or 0) - (old_m.get("elapsed_seconds") or 0),
            }
        if changes:
            changed.append({"name": name, "changes": changes})

    return {"added": added, "removed": removed, "changed": changed}


def print_human_diff(diff: Dict[str, Any]):
    if diff["added"]:
        print("Added modules:")
        for m in diff["added"]:
            print(f"  + {m}")

    if diff["removed"]:
        print("Removed modules:")
        for m in diff["removed"]:
            print(f"  - {m}")

    if diff["changed"]:
        print("Changed modules:")
        for c in diff["changed"]:
            print(f"  ~ {c['name']}:")
            for key, val in c["changes"].items():
                if key == "status":
                    print(f"      status: {val['from']} -> {val['to']}")
                elif key == "elapsed_seconds":
                    delta = val.get("delta", 0)
                    direction = "+" if delta > 0 else ""
                    print(f"      duration: {val['from']}s -> {val['to']}s ({direction}{delta}s)")
                elif key == "artifact":
                    print(f"      artifact: {val['from']} -> {val['to']}")
                else:
                    print(f"      {key}: {val['from']} -> {val['to']}")

    if not any([diff["added"], diff["removed"], diff["changed"]]):
        print("No differences found.")


def print_json_diff(diff: Dict[str, Any]):
    print(json.dumps(diff, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description="Compare two diagnostic metadata files")
    parser.add_argument("old_file", help="Path to old diagnostic JSON")
    parser.add_argument("new_file", help="Path to new diagnostic JSON")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output mode")
    return parser.parse_args()


def main():
    args = parse_args()

    old_data = load_diagnostic(args.old_file)
    if old_data is None:
        return 1

    new_data = load_diagnostic(args.new_file)
    if new_data is None:
        return 1

    old_modules = old_data.get("modules", [])
    new_modules = new_data.get("modules", [])

    diff = compare_module_dicts(old_modules, new_modules)

    if args.json:
        print_json_diff(diff)
    else:
        print_human_diff(diff)

    if not isinstance(diff["changed"], list):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())