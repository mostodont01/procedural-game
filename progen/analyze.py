"""Checks and metrics for a generated world (D14)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .generate import ROLES, goodness
from .model import HAND, MACHINE_TIER, Recipe, World


@dataclass
class Validation:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(world: World) -> Validation:
    v = Validation()
    items = world.items
    start = {p.index: p.start_tier for p in world.planets}

    for r in world.recipes:
        for name in list(r.inputs) + list(r.outputs):
            if name not in items:
                v.errors.append(f"recipe '{r.name}' uses unknown item '{name}'")
        if r.machine not in HAND and r.machine not in MACHINE_TIER:
            v.errors.append(f"recipe '{r.name}' uses unknown machine '{r.machine}'")
    if v.errors:
        return v

    # Reachability: simulate tier by tier. Tier-0 recipes can be hand-crafted.
    produced: set[str] = set()
    for t, tier in enumerate(world.tiers):
        reached = {i for i, s in start.items() if s <= t}
        ran: set[str] = set()
        changed = True
        while changed:
            changed = False
            for r in world.recipes:
                if r.tier > t or id(r) in ran:
                    continue
                if r.kind == "extract" and not reached.intersection(r.planets or []):
                    continue
                machine_ok = (r.machine in HAND or r.machine in produced
                              or (t == 0 and MACHINE_TIER[r.machine] == 0))
                if machine_ok and all(i in produced for i in r.inputs):
                    ran.add(id(r))
                    new = set(r.outputs) - produced
                    if new:
                        produced |= new
                    changed = True
        if tier.milestone not in produced:
            v.errors.append(f"tier {t}: milestone '{tier.milestone}' is not reachable")
        for r in world.recipes:
            if r.tier == t and id(r) not in ran:
                v.errors.append(f"tier {t}: recipe '{r.name}' can't run at its own tier")

    # No dead ends: everything except milestones and waste is used by something.
    consumed = {i for r in world.recipes for i in r.inputs} | {r.machine for r in world.recipes}
    for it in items.values():
        if it.kind not in ("milestone", "waste") and it.name not in consumed:
            v.errors.append(f"dead end: {it.kind} '{it.name}' is never used")
    for it in items.values():
        if it.kind == "waste" and it.name not in consumed:
            v.warnings.append(f"waste to dispose of: {it.name}")

    # Parts really meet their role requirement.
    mats = {m.name: m for m in world.materials}
    for role, steps in world.roles.items():
        prop, op, _, _ = ROLES[role]
        for s in steps:
            if goodness(mats[s.material], prop, op) < (s.threshold if op == ">=" else -s.threshold):
                v.errors.append(f"{s.part} doesn't meet {role} requirement {prop} {op} {s.threshold}")

    # Needs chain: only the key material solves the hazard before the planet is reached.
    for n in world.needs:
        h = n.hazard
        key = mats[n.key_material]
        thr = n.threshold if h.op == ">=" else -n.threshold
        if goodness(key, h.prop, h.op) < thr:
            v.errors.append(f"need of planet {n.planet}: key {key.name} fails its own threshold")
        rivals = [m.name for m in world.materials if m.name != key.name
                  and m.tier < world.planets[n.planet].start_tier and goodness(m, h.prop, h.op) >= thr]
        if rivals:
            v.errors.append(f"need of planet {n.planet}: also solved by {', '.join(rivals)}")
    for p in world.planets[1:]:
        if not any(n.planet == p.index for n in world.needs):
            v.errors.append(f"planet {p.index} has no need link")
    return v


# ------------------------------------------------------------- metrics ---


def primary_recipes(world: World) -> dict[str, Recipe]:
    prim: dict[str, Recipe] = {}
    for r in world.recipes:
        if r.kind == "regen":
            continue
        main = next(iter(r.outputs))  # first output is the main product
        prim.setdefault(main, r)
    return prim


def closure(world: World, item: str, prim: dict[str, Recipe] | None = None) -> set[str]:
    """Names of all recipes (incl. machine builds) needed to make `item`."""
    prim = prim or primary_recipes(world)
    seen: set[str] = set()
    stack = [item]
    while stack:
        it = stack.pop()
        r = prim.get(it)
        if r is None or r.name in seen:
            continue
        seen.add(r.name)
        stack.extend(r.inputs)
        if r.machine not in HAND:
            stack.append(r.machine)
    return seen


def raw_demand(world: World, item: str, qty: float = 1.0) -> dict[str, float]:
    prim = primary_recipes(world)
    acc: dict[str, float] = defaultdict(float)

    def walk(it: str, q: float) -> None:
        r = prim[it]
        if r.kind == "extract":
            acc[it] += q
            return
        runs = q / r.outputs[it]
        for inp, n in r.inputs.items():
            walk(inp, n * runs)

    walk(item, qty)
    return dict(sorted(acc.items(), key=lambda kv: -kv[1]))


# Playtime model. PLACEHOLDER: the constants are guesses, chosen so typical worlds
# land near the DESIGN.md targets. Useful for comparing planets and seeds (relative
# size, outliers), not as a real prediction. Real calibration needs playtests (D14).
TIER_BASE_H = 6.0  # exploring, rebuilding, waiting per tier
RECIPE_COST_H = {"extract": 1.5, "process": 2.0, "alloy": 3.0, "part": 1.5, "build": 0.5,
                 "component": 2.5, "milestone": 1.0, "gear": 3.0}
TIER_GROWTH = 1.04  # later tiers mean bigger factories per recipe
HOME_FACTOR = 1.5  # first planet: every system is new to the player, plus the tutorial
ARRIVAL_H = 6.0  # surveying and bootstrapping a new planet


def estimate_hours(world: World) -> list[float]:
    prim = primary_recipes(world)
    kinds = {r.name: r.kind for r in world.recipes}
    seen: set[str] = set()
    per_planet = [0.0 for _ in world.planets]
    for t, tier in enumerate(world.tiers):
        need = closure(world, tier.milestone, prim) - seen
        seen |= need
        hours = TIER_BASE_H + sum(RECIPE_COST_H.get(kinds[n], 1.0) for n in need) * TIER_GROWTH ** t
        per_planet[tier.planet] += hours
    per_planet[0] *= HOME_FACTOR
    for i in range(1, len(per_planet)):
        per_planet[i] += ARRIVAL_H
    return [round(h, 1) for h in per_planet]


def bottlenecks(world: World) -> list[str]:
    """Most demanded raw resource for each planet's final milestone."""
    out = []
    for p in world.planets:
        last = [t for t in world.tiers if t.planet == p.index][-1]
        demand = raw_demand(world, last.milestone)
        out.append(next(iter(demand)) if demand else "-")
    return out
