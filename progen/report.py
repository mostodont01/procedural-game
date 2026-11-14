"""Text, JSON and Graphviz output."""

from __future__ import annotations

import dataclasses
import json

from .analyze import bottlenecks, estimate_hours, validate
from .generate import ROLES, planet_variants
from .model import PROPERTIES, World

SHORT = {"strength": "str", "density": "dens", "conductivity": "cond",
         "heat_resistance": "heat", "reactivity": "react", "transparency": "trans"}


def _table(rows: list[list[str]], header: list[str]) -> str:
    widths = [max(len(str(x)) for x in col) for col in zip(header, *rows)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*header), fmt.format(*["-" * w for w in widths])]
    lines += [fmt.format(*map(str, r)) for r in rows]
    return "\n".join("  " + ln for ln in lines)


def _planet_row(p) -> list[str]:
    return [p.index, p.name, p.kind, f"{p.temperature_c} °C", f"{p.gravity_g} g", p.atmosphere,
            "yes" if p.water else "no", f"{p.day_hours:g} h", p.start_tier,
            p.hazard.tag if p.hazard else "-"]


def needs_lines(world: World) -> list[str]:
    out = []
    for n in world.needs:
        p = world.planets[n.planet]
        src = world.planets[n.source_planet]
        where = f"only on {src.name}" + (" (deep, needs Deep Drill)" if n.source_planet == 0 else "")
        out.append(
            f"  {p.name} ({p.kind}): {n.hazard.description}\n"
            f"    -> {n.gear} needs {n.gear_part}: {n.hazard.prop} {n.hazard.op} {n.threshold:g}\n"
            f"    -> only {n.key_material} qualifies, made from {n.key_resource}, {where}"
        )
    return out


def world_text(world: World, show_recipes: bool = False) -> str:
    v = validate(world)
    hours = estimate_hours(world)
    necks = bottlenecks(world)
    s = [f"World seed {world.seed}: {world.system_name}, {len(world.planets)} planets, "
         f"{len(world.tiers)} tiers, {len(world.recipes)} recipes", ""]
    s.append("PLANETS (in order of reach)")
    s.append(_table([_planet_row(p) for p in world.planets],
                    ["#", "name", "kind", "temp", "grav", "atmo", "water", "day", "tier", "hazard"]))
    s += ["", "RESOURCES"]
    s.append(_table([[r.name, r.category, ", ".join(world.planets[i].name for i in r.planets),
                      r.extractor, r.tier] for r in world.resources],
                    ["name", "category", "found on", "extractor", "tier"]))
    s += ["", "MATERIALS (properties 0-100; key materials go beyond 90 / below 8)"]
    s.append(_table([[m.name, m.category, m.tier, *[f"{m.props[p]:g}" for p in PROPERTIES]]
                     for m in sorted(world.materials, key=lambda m: m.tier)],
                    ["name", "type", "tier", *[SHORT[p] for p in PROPERTIES]]))
    s += ["", "WHAT EACH PART IS MADE OF (changes when the requirement outgrows the material)"]
    for role, steps in world.roles.items():
        prop, op, label, _ = ROLES[role]
        chain = "  ->  ".join(f"T{x.tier} {x.material} ({prop} {op} {x.threshold:g})" for x in steps)
        s.append(f"  {label:<10} {chain}")
    s += ["", "TIERS"]
    for t in world.tiers:
        mach = f" machines: {', '.join(t.machines)};" if t.machines else ""
        s.append(f"  T{t.index} [{world.planets[t.planet].name}]{mach} "
                 f"components: {', '.join(t.components)} -> {t.milestone}")
    s += ["", "NEEDS CHAIN (the progression's story)"] + needs_lines(world)
    s += ["", "ESTIMATE (placeholder model, compare seeds with it, don't trust the absolute hours)"]
    for p, h, neck in zip(world.planets, hours, necks):
        s.append(f"  {p.name:<8} ~{h:>5.0f} h   bottleneck raw: {neck}")
    if show_recipes:
        s += ["", "RECIPES"]
        for r in world.recipes:
            ins = " + ".join(f"{q} {i}" for i, q in r.inputs.items()) or "(node)"
            outs = " + ".join(f"{q} {o}" for o, q in r.outputs.items())
            s.append(f"  T{r.tier} {r.kind:<9} [{r.machine}] {ins} -> {outs}")
    s += ["", f"VALIDATION: {'OK' if v.ok else 'FAILED'} "
              f"({len(v.errors)} errors, {len(v.warnings)} warnings)"]
    s += [f"  error: {e}" for e in v.errors]
    s += [f"  note: {w}" for w in v.warnings]
    return "\n".join(s)


def planet_text(world: World, index: int) -> str:
    p = world.planets[index]
    s = [f"Planet {p.index}: {p.name} ({p.kind}) in {world.system_name}, seed {world.seed}",
         f"  {p.temperature_c} °C, {p.gravity_g} g, atmosphere {p.atmosphere}, "
         f"water {'yes' if p.water else 'no'}, {p.day_hours:g} h day, reached at tier {p.start_tier}",
         "", "CONSTRAINTS"]
    s += [f"  {'*' if p.hazard is h else '-'} {h.description}" for h in p.traits] or ["  (none)"]
    if p.hazard:
        s.append("  (* = drives the needs chain)")
    s += ["", "LOCAL RESOURCES"]
    s += [f"  {r.name} ({r.category}, {r.extractor})" for r in world.resources if p.index in r.planets]
    need = next((n for n in world.needs if n.planet == p.index), None)
    if need:
        s += ["", "TO GET HERE"] + needs_lines(world)[world.needs.index(need)].splitlines()
    unlocks = next((n for n in world.needs if n.source_planet == p.index), None)
    if unlocks:
        s += ["", "WHY COME HERE",
              f"  {unlocks.key_resource} -> {unlocks.key_material} is the only way to reach "
              f"{world.planets[unlocks.planet].name}"]
    s += ["", "LOCAL RECIPE VARIANTS AND RULES"]
    s += [f"  - {x}" for x in planet_variants(world, p)] or ["  (none)"]
    return "\n".join(s)


def world_json(world: World) -> str:
    return json.dumps(dataclasses.asdict(world), indent=1, ensure_ascii=False)


COLORS = {"raw": "#c9a66b", "material": "#8fb3d9", "part": "#a6d49f", "component": "#e8c46a",
          "machine": "#b9b9b9", "milestone": "#e07a5f", "gear_part": "#c39bd3", "gear": "#9b59b6",
          "waste": "#eeeeee"}


def world_dot(world: World, max_tier: int | None = None, machines: bool = False) -> str:
    keep = {n for n, it in world.items.items() if max_tier is None or it.tier <= max_tier}
    if not machines:
        keep = {n for n in keep if world.items[n].kind != "machine"}
    lines = ["digraph world {", "  rankdir=LR; node [shape=box, style=filled, fontname=Helvetica];",
             f'  label="{world.system_name} (seed {world.seed})";']
    for t in sorted({it.tier for it in world.items.values()}):
        names = [n for n in keep if world.items[n].tier == t]
        if not names:
            continue
        lines.append(f'  subgraph cluster_t{t} {{ label="Tier {t}"; color="#999999";')
        for n in sorted(names):
            lines.append(f'    "{n}" [fillcolor="{COLORS[world.items[n].kind]}"];')
        lines.append("  }")
    for r in world.recipes:
        for o in r.outputs:
            for i in r.inputs:
                if i in keep and o in keep:
                    lines.append(f'  "{i}" -> "{o}";')
    lines.append("}")
    return "\n".join(lines)
