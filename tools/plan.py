"""Checks and updates the decision table in DESIGN-PLAN.md.

    python tools/plan.py check          # verify the process rules (run in CI)
    python tools/plan.py next           # decisions that can be worked on / locked now
    python tools/plan.py impact D03     # what goes stale if D03 changes
    python tools/plan.py stale D03      # mark everything depending on D03 as stale
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PLAN = Path(__file__).resolve().parent.parent / "DESIGN-PLAN.md"
STATUSES = ("open", "draft", "locked", "stale")
ROW = re.compile(r"^\|\s*(D\d+)\s*\|([^|]*)\|([^|]*)\|\s*(\w+)\s*\|\s*$")


@dataclass
class Decision:
    id: str
    title: str
    deps: list[str]
    status: str
    line: int  # index into the file's lines
    order: int = field(default=0)


def parse(text: str) -> list[Decision]:
    decisions = []
    for i, line in enumerate(text.splitlines()):
        m = ROW.match(line)
        if not m:
            continue
        dep_text = m.group(3).strip()
        deps = [] if dep_text in ("", "-") else [d.strip() for d in dep_text.split(",")]
        decisions.append(
            Decision(m.group(1), m.group(2).strip(), deps, m.group(4), i, len(decisions))
        )
    return decisions


def dependents(decisions: list[Decision], target: str) -> list[str]:
    """All decisions that depend on `target`, directly or indirectly, in table order."""
    hit = {target}
    for d in decisions:  # deps point backwards, so one pass in order is enough
        if any(dep in hit for dep in d.deps):
            hit.add(d.id)
    return [d.id for d in decisions if d.id in hit and d.id != target]


def check(decisions: list[Decision]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    by_id = {d.id: d for d in decisions}
    if len(by_id) != len(decisions):
        errors.append("duplicate decision IDs")
    for d in decisions:
        if d.status not in STATUSES:
            errors.append(f"{d.id}: unknown status '{d.status}'")
        for dep in d.deps:
            if dep not in by_id:
                errors.append(f"{d.id}: depends on unknown {dep}")
            elif by_id[dep].order >= d.order:
                errors.append(f"{d.id}: depends on {dep}, which is not earlier in the table")
            elif d.status == "locked" and by_id[dep].status != "locked":
                errors.append(
                    f"{d.id} is locked but depends on {dep} ({by_id[dep].status})"
                )
    stale = [d.id for d in decisions if d.status == "stale"]
    if stale:
        warnings.append("stale, review before locking anything else: " + ", ".join(stale))
    return errors, warnings


def ready(decisions: list[Decision]) -> list[Decision]:
    """Not-yet-locked decisions whose dependencies are all locked."""
    by_id = {d.id: d for d in decisions}
    stale = [d for d in decisions if d.status == "stale"]
    if stale:  # change rule: stale items come first
        return [d for d in stale if all(by_id[x].status == "locked" for x in d.deps)]
    return [
        d
        for d in decisions
        if d.status != "locked" and all(by_id[x].status == "locked" for x in d.deps)
    ]


def mark_stale(text: str, target: str) -> tuple[str, list[str]]:
    decisions = parse(text)
    lines = text.splitlines(keepends=True)
    changed = []
    for d in decisions:
        if d.id in dependents(decisions, target) and d.status in ("locked", "draft"):
            line = lines[d.line]
            idx = line.rstrip().rstrip("|").rstrip().rfind(d.status)
            lines[d.line] = line[:idx] + "stale" + line[idx + len(d.status):]
            changed.append(d.id)
    return "".join(lines), changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("command", choices=["check", "next", "impact", "stale"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--file", type=Path, default=PLAN)
    args = ap.parse_args(argv)

    text = args.file.read_text()
    decisions = parse(text)
    ids = {d.id for d in decisions}
    if args.command in ("impact", "stale") and args.id not in ids:
        ap.error(f"give a decision ID, one of {min(ids)}..{max(ids)}")

    if args.command == "check":
        errors, warnings = check(decisions)
        for w in warnings:
            print("warning:", w)
        for e in errors:
            print("error:", e)
        if not errors:
            counts = {s: sum(d.status == s for d in decisions) for s in STATUSES}
            print(f"ok: {len(decisions)} decisions, " + ", ".join(f"{n} {s}" for s, n in counts.items()))
        return 1 if errors else 0
    if args.command == "next":
        for d in ready(decisions):
            print(f"{d.id}  {d.title}  [{d.status}]")
        return 0
    if args.command == "impact":
        deps = dependents(decisions, args.id)
        print(f"Changing {args.id} makes {len(deps)} decisions stale:")
        titles = {d.id: d.title for d in decisions}
        for x in deps:
            print(f"  {x}  {titles[x]}")
        return 0
    new_text, changed = mark_stale(text, args.id)
    args.file.write_text(new_text)
    print("marked stale:", ", ".join(changed) if changed else "nothing (no locked/draft dependents)")
    print("Add a line to the change log in DESIGN-PLAN.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
