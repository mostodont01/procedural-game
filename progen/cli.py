"""Command line: `gen world`, `gen planet`, `gen graph`, `gen compare`, `gen check`."""

from __future__ import annotations

import argparse
import shutil
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

from .analyze import bottlenecks, estimate_hours, validate
from .generate import generate_world
from .report import planet_text, world_dot, world_json, world_text


def cmd_world(a) -> int:
    w = generate_world(a.seed)
    print(world_json(w) if a.json else world_text(w, a.recipes))
    return 0


def cmd_planet(a) -> int:
    w = generate_world(a.seed)
    if not 0 <= a.planet < len(w.planets):
        print(f"seed {a.seed} has planets 0..{len(w.planets) - 1}", file=sys.stderr)
        return 2
    print(planet_text(w, a.planet))
    return 0


def cmd_graph(a) -> int:
    w = generate_world(a.seed)
    dot = world_dot(w, a.max_tier, a.machines)
    out = Path(a.output)
    if out.suffix == ".dot":
        out.write_text(dot)
    elif shutil.which("dot"):
        subprocess.run(["dot", f"-T{out.suffix[1:]}", "-o", str(out)], input=dot, text=True, check=True)
    else:
        out = out.with_suffix(".dot")
        out.write_text(dot)
        print("Graphviz 'dot' not found, wrote DOT source instead "
              "(install graphviz to render SVG/PNG).", file=sys.stderr)
    print(f"wrote {out}")
    return 0


def _summary(seed: int) -> dict[str, str]:
    w = generate_world(seed)
    roles = {k: " > ".join(s.material for s in v) for k, v in w.roles.items()}
    return {
        "planets": " > ".join(f"{p.name} ({p.kind})" for p in w.planets),
        "needs": " > ".join(f"{n.hazard.tag}: {n.key_material}" for n in w.needs),
        **{f"part: {k}": v for k, v in roles.items()},
        "bottlenecks": " > ".join(bottlenecks(w)),
        "hours/planet": ", ".join(f"{h:.0f}" for h in estimate_hours(w)),
    }


def cmd_compare(a) -> int:
    sums = [_summary(s) for s in a.seeds]
    keys = list(dict.fromkeys(k for s in sums for k in s))
    for k in keys:
        print(k)
        for seed, s in zip(a.seeds, sums):
            print(f"  seed {seed:<6} {s.get(k, '-')}")
    return 0


def cmd_check(a) -> int:
    failed = []
    hours_home, hours_other = [], []
    plate_types: Counter[str] = Counter()
    with_alloy = 0
    for seed in range(a.start, a.start + a.seeds):
        w = generate_world(seed)
        v = validate(w)
        if not v.ok:
            failed.append((seed, v.errors[:3]))
        h = estimate_hours(w)
        hours_home.append(h[0])
        hours_other += h[1:]
        mats = {m.name: m for m in w.materials}
        plate_types[mats[w.roles["plate"][0].material].category] += 1
        with_alloy += any(m.category == "alloy" for m in w.materials)
    print(f"{a.seeds} worlds, {a.seeds - len(failed)} valid")
    for seed, errs in failed[:10]:
        print(f"  seed {seed}: " + "; ".join(errs))

    def rng(xs):
        return f"median {statistics.median(xs):.0f} h, range {min(xs):.0f}-{max(xs):.0f} h"

    print(f"home planet estimate: {rng(hours_home)}  (target 150+)")
    print(f"other planets:        {rng(hours_other)}  (target 30-80)")
    types = ", ".join(f"{k} {100 * v / a.seeds:.0f}%" for k, v in plate_types.most_common())
    print(f"first plate is made of: {types}")
    print(f"worlds that need an alloy: {100 * with_alloy / a.seeds:.0f}%")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gen", description="Procedural progression generator (milestone 0).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("world", help="print a world's planets, materials, tiers and needs chain")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--recipes", action="store_true", help="also list every recipe")
    p.add_argument("--json", action="store_true", help="dump the whole world as JSON")
    p.set_defaults(fn=cmd_world)

    p = sub.add_parser("planet", help="one planet: constraints, local resources, variants")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--planet", type=int, default=0)
    p.set_defaults(fn=cmd_planet)

    p = sub.add_parser("graph", help="draw the recipe graph (DOT, or SVG/PNG with Graphviz)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("-o", "--output", default="graph.svg")
    p.add_argument("--max-tier", type=int)
    p.add_argument("--machines", action="store_true", help="include machine items")
    p.set_defaults(fn=cmd_graph)

    p = sub.add_parser("compare", help="compare worlds side by side")
    p.add_argument("seeds", type=int, nargs="+")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("check", help="validate many seeds and print statistics")
    p.add_argument("--seeds", type=int, default=200)
    p.add_argument("--start", type=int, default=0)
    p.set_defaults(fn=cmd_check)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
