"""Generates a world: planets, resources, materials, recipes, tiers and the needs chain.

Order of generation (each step only reads what earlier steps made):

1. planets and their hazards       (D05, D08)
2. resources and where they are    (D07)
3. materials with properties       (D06), incl. the key materials of the needs chain
4. alloys
5. part roles per tier             (D06/D10: "wire needs conductivity >= X")
6. machines, components, milestones (D09, D10)
7. gear for each planet's hazard   (D12)
8. prune dead ends, add byproducts and a catalyst loop
"""

from __future__ import annotations

import math
import random

from .model import (
    HAND,
    MACHINE_TIER,
    MACHINES,
    PROPERTIES,
    Hazard,
    Item,
    Material,
    NeedLink,
    Planet,
    Recipe,
    Resource,
    RoleStep,
    Tier,
    World,
)
from .names import NameGen, rng_for

TIERS_HOME = 4  # tiers 0..3 on the home planet
TIERS_PER_PLANET = 2

# ---------------------------------------------------------------- planets ---

KINDS = {
    "earthlike": dict(temp=(5, 25), g=(0.9, 1.1), atm=["breathable"], water=1.0, day=(18, 30)),
    "rocky": dict(temp=(-60, 80), g=(0.3, 1.4), atm=["none", "thin", "toxic"], water=0.3, day=(10, 80)),
    "ice": dict(temp=(-230, -90), g=(0.2, 1.0), atm=["none", "thin"], water=1.0, day=(8, 200)),
    "lava": dict(temp=(180, 600), g=(0.6, 1.8), atm=["toxic", "corrosive", "thin"], water=0.0, day=(5, 40)),
    "desert": dict(temp=(30, 160), g=(0.5, 1.3), atm=["thin", "breathable", "toxic"], water=0.1, day=(15, 120)),
    "ocean": dict(temp=(-10, 50), g=(0.8, 1.9), atm=["breathable", "toxic", "thin"], water=1.0, day=(10, 40)),
    "toxic": dict(temp=(20, 250), g=(0.7, 1.6), atm=["corrosive", "toxic"], water=0.4, day=(20, 300)),
    "gas_giant": dict(temp=(-180, -60), g=(1.8, 3.0), atm=["dense"], water=0.0, day=(8, 16)),
}

HAZARDS = {
    "extreme_cold": ("conductivity", "<=", "Extreme cold ({t} °C): suits and machines lose heat, need insulation"),
    "extreme_heat": ("heat_resistance", ">=", "Extreme heat ({t} °C): everything exposed needs heat-resistant plating"),
    "corrosive": ("reactivity", "<=", "Corrosive atmosphere: exposed materials dissolve, need inert linings"),
    "toxic": ("reactivity", ">=", "Toxic atmosphere: air must be scrubbed by a reactive filter"),
    "crushing_pressure": ("strength", ">=", "No surface, crushing pressure: only a reinforced orbital station"),
    "high_gravity": ("strength", ">=", "High gravity ({g} g): landers and structures need strong struts"),
    "vacuum": ("density", ">=", "No atmosphere: hard radiation, habitats need dense shielding"),
    "no_water": (None, None, "No liquid water: washing / water-cooled recipes need local variants"),
    "long_night": (None, None, "Long nights ({d} h days): solar fails for hours, needs storage or other power"),
    "low_gravity": (None, None, "Low gravity ({g} g): cheap launches, light structures"),
}

GEAR = {
    "extreme_cold": ("Insulation Layer", "Cryo Suit"),
    "extreme_heat": ("Thermal Plating", "Heat Suit"),
    "corrosive": ("Inert Liner", "Corrosion Suit"),
    "toxic": ("Scrubber Filter", "Rebreather"),
    "crushing_pressure": ("Pressure Hull Plate", "Orbital Station Kit"),
    "high_gravity": ("Lander Strut", "Heavy Lander"),
    "vacuum": ("Radiation Lining", "Shielded Habitat"),
}


def planet_traits(p: Planet) -> list[Hazard]:
    tags = []
    if p.temperature_c < -80:
        tags.append("extreme_cold")
    if p.temperature_c > 120:
        tags.append("extreme_heat")
    if p.atmosphere == "corrosive":
        tags.append("corrosive")
    if p.atmosphere == "toxic":
        tags.append("toxic")
    if p.atmosphere == "dense":
        tags.append("crushing_pressure")
    if p.atmosphere == "none":
        tags.append("vacuum")
    if p.gravity_g > 1.5 and p.kind != "gas_giant":
        tags.append("high_gravity")
    if p.gravity_g < 0.5:
        tags.append("low_gravity")
    if not p.water:
        tags.append("no_water")
    if p.day_hours > 60:
        tags.append("long_night")
    out = []
    for tag in tags:
        prop, op, desc = HAZARDS[tag]
        desc = desc.format(t=p.temperature_c, g=p.gravity_g, d=round(p.day_hours))
        out.append(Hazard(tag, desc, prop, op))
    return out


def gen_planets(rng: random.Random, names: NameGen) -> list[Planet]:
    n = rng.randint(4, 6)
    kinds = ["earthlike"]
    for _ in range(1, n):
        pool = [k for k in KINDS if k != "earthlike" and not (k == "gas_giant" and k in kinds)]
        kinds.append(rng.choice(pool))
    planets = []
    for i, kind in enumerate(kinds):
        s = KINDS[kind]
        p = Planet(
            index=i,
            name=names.root(4, 7),
            kind=kind,
            temperature_c=rng.randint(*s["temp"]),
            gravity_g=round(rng.uniform(*s["g"]), 2),
            atmosphere=rng.choice(s["atm"]),
            water=rng.random() < s["water"],
            day_hours=round(rng.uniform(*s["day"]), 1),
            start_tier=0 if i == 0 else TIERS_HOME + TIERS_PER_PLANET * (i - 1),
        )
        p.traits = planet_traits(p)
        if i > 0:
            if not any(h.prop for h in p.traits):
                p.atmosphere = "none"  # every later planet must be a problem to solve
                p.traits = planet_traits(p)
            options = [h for h in p.traits if h.prop]
            used = {q.hazard.tag for q in planets if q.hazard}
            fresh = [h for h in options if h.tag not in used]
            p.hazard = rng.choice(fresh or options)
        planets.append(p)
    return planets


# -------------------------------------------------------------- resources ---

CAT_WEIGHTS = {
    "rocky": {"metal_ore": 3, "mineral": 2, "crystal": 1},
    "ice": {"crystal": 2, "liquid": 2, "gas": 1, "mineral": 1},
    "lava": {"metal_ore": 3, "mineral": 2, "crystal": 1},
    "desert": {"mineral": 3, "crystal": 2, "metal_ore": 1},
    "ocean": {"liquid": 3, "organic": 2, "mineral": 1},
    "toxic": {"liquid": 2, "gas": 2, "organic": 1},
    "gas_giant": {"gas": 1},
}
RES_NAME = {
    "metal_ore": "{} Ore", "mineral": "{}ite", "crystal": "{} Crystal",
    "gas": "{}on Gas", "liquid": "{}ol", "organic": "{} Moss",
}
MAT_NAME = {
    "metal_ore": ("{}ium", "metal"), "mineral": ("{} Ceramic", "ceramic"),
    "crystal": ("{} Glass", "glass"), "gas": ("{}on Polymer", "polymer"),
    "liquid": ("{}ol Resin", "resin"), "organic": ("{} Fiber", "fiber"),
}
PROCESSOR = {
    "metal_ore": "Smelter", "mineral": "Smelter", "crystal": "Constructor",
    "gas": "Refinery", "liquid": "Refinery", "organic": "Refinery",
}
# (low, high) per property, in the order of PROPERTIES
PROFILES = {
    "metal_ore": [(50, 85), (50, 85), (55, 90), (35, 75), (20, 70), (8, 15)],
    "mineral": [(30, 60), (35, 60), (8, 25), (60, 90), (10, 40), (10, 40)],
    "crystal": [(15, 45), (25, 50), (10, 60), (40, 80), (8, 30), (55, 90)],
    "gas": [(15, 45), (8, 25), (8, 30), (10, 40), (30, 80), (30, 70)],
    "liquid": [(20, 50), (15, 40), (10, 40), (20, 50), (40, 90), (20, 60)],
    "organic": [(30, 70), (8, 30), (8, 25), (10, 35), (20, 60), (10, 30)],
}
PROP_MIN, PROP_MAX = 8.0, 90.0  # normal materials; key materials go beyond


def _weighted(rng: random.Random, weights: dict[str, int]) -> str:
    keys = list(weights)
    return rng.choices(keys, [weights[k] for k in keys])[0]


def _extractor(cat: str, kind: str, deep: bool) -> str:
    if kind == "gas_giant":
        return "Orbital Harvester"
    if cat in ("gas", "liquid"):
        return "Pump"
    return "Deep Drill" if deep else "Miner"


def gen_resources(rng, names, planets) -> tuple[list[Resource], dict[int, str]]:
    res: list[Resource] = []
    keys: dict[int, str] = {}  # planet k -> resource whose material solves planet k's hazard

    def make(cat: str, planet: int, deep: bool = False) -> Resource:
        root = names.root()
        r = Resource(RES_NAME[cat].format(root), root, cat, [planet],
                     _extractor(cat, planets[planet].kind, deep), deep)
        res.append(r)
        return r

    for cat in ("metal_ore", "metal_ore", "mineral", "crystal", "organic", "liquid", "gas"):
        make(cat, 0)
    home_count = len(res)

    for k in range(1, len(planets)):
        src = planets[k - 1]
        if src.index == 0:  # the first need is solved by a deep resource on the home planet
            r = make(rng.choice(["metal_ore", "mineral", "crystal"]), 0, deep=True)
        else:
            r = make(_weighted(rng, CAT_WEIGHTS[src.kind]), src.index)
        keys[k] = r.name

    for p in planets[1:]:
        for _ in range(rng.randint(1, 2)):
            r = make(_weighted(rng, CAT_WEIGHTS[p.kind]), p.index)
            later = [q for q in planets[p.index + 1:] if q.kind != "gas_giant"]
            if later and p.kind != "gas_giant" and rng.random() < 0.3:
                r.planets.append(rng.choice(later).index)
        if p.kind != "gas_giant":  # common home resources show up elsewhere too
            for r in res[:home_count]:
                if r.category in CAT_WEIGHTS[p.kind] and rng.random() < 0.3:
                    r.planets.append(p.index)

    water = [p.index for p in planets if p.water]
    res.append(Resource("Water", "Water", "water", water, "Water Extractor"))

    for r in res:
        first = min(planets[i].start_tier for i in r.planets)
        r.tier = max(first, MACHINE_TIER[r.extractor])
    return res, keys


# -------------------------------------------------------------- materials ---


def _clamp(v: float) -> float:
    return round(min(PROP_MAX, max(PROP_MIN, v)), 1)


def key_value(k: int, op: str) -> float:
    """Key materials are beyond the normal range and escalate along the chain,
    so a later key always beats an earlier one in the same property."""
    return round(90.5 + 1.3 * k, 1) if op == ">=" else round(7.5 - 0.9 * k, 1)


def gen_materials(rng, resources, planets, keys) -> list[Material]:
    key_for = {name: k for k, name in keys.items()}
    mats = []
    for r in resources:
        if r.category == "water":
            continue
        props = {p: _clamp(rng.uniform(lo, hi)) for p, (lo, hi) in zip(PROPERTIES, PROFILES[r.category])}
        if rng.random() < 0.4:  # a quirk: this world's "metal" may be oddly weak, a glass may conduct...
            q = rng.choice(PROPERTIES)
            props[q] = _clamp(props[q] + rng.choice((-1, 1)) * rng.uniform(15, 30))
        if r.name in key_for:
            k = key_for[r.name]
            h = planets[k].hazard
            props[h.prop] = key_value(k, h.op)
        fmt, cat = MAT_NAME[r.category]
        tier = max(r.tier, MACHINE_TIER[PROCESSOR[r.category]])
        mats.append(Material(fmt.format(r.root), r.root, cat, props, [r.name], tier, r.planets[0]))
    return mats


def gen_alloys(rng, mats, n_planets) -> list[Material]:
    """Alloys are made to be the best material for one property at their tier,
    so they become necessary when requirements get high."""
    alloys: list[Material] = []
    names = {m.name for m in mats}
    for _ in range(2 + n_planets // 2):
        a, b = rng.sample(mats, 2)
        tier = max(a.tier, b.tier, MACHINE_TIER["Foundry"])
        props = {p: (a.props[p] + b.props[p]) / 2 for p in PROPERTIES}
        up = rng.choice(PROPERTIES)
        sign = 1 if up != "density" or rng.random() < 0.5 else -1  # light alloys too
        rivals = [m.props[up] for m in mats + alloys if m.tier <= tier]
        target = max(rivals) + rng.uniform(2, 6) if sign > 0 else min(rivals) - rng.uniform(2, 6)
        if not PROP_MIN < target < PROP_MAX:
            continue  # nothing to beat without breaking a key material's lead
        props[up] = target
        down = rng.choice([p for p in PROPERTIES if p != up])
        props[down] -= rng.uniform(5, 15)  # every alloy has a trade-off
        props = {p: _clamp(v) for p, v in props.items()}
        root = a.root[:3] + b.root[-3:].lower()
        name = f"{root} Alloy"
        if name in names:
            continue
        names.add(name)
        alloys.append(Material(name, root, "alloy", props, [a.name, b.name], tier,
                               max(a.home_planet, b.home_planet)))
    return alloys


# ------------------------------------------------------------ part roles ---

ROLES = {  # role: (property, op, label, first tier)
    "plate": ("strength", ">=", "Plate", 0),
    "wire": ("conductivity", ">=", "Wire", 0),
    "frame": ("density", "<=", "Frame", 0),
    "heat_shield": ("heat_resistance", ">=", "Heat Tile", 0),
    "seal": ("reactivity", "<=", "Seal", 1),
    "lens": ("transparency", ">=", "Lens", 1),
    "catalyst": ("reactivity", ">=", "Catalyst", 2),
    "shielding": ("density", ">=", "Shielding", 2),
}


def goodness(m: Material, prop: str, op: str) -> float:
    return m.props[prop] if op == ">=" else -m.props[prop]


def assign_roles(rng, mats, n_tiers) -> tuple[dict[str, list[RoleStep]], list[dict[str, str]]]:
    """For each tier and role, the requirement rises and the cheapest material
    that meets it is used. Which material that is depends entirely on the world."""
    chains: dict[str, list[RoleStep]] = {r: [] for r in ROLES}
    current: list[dict[str, str]] = []
    last_thr: dict[str, float] = {}
    for t in range(n_tiers):
        avail = [m for m in mats if m.tier <= t]
        cur = {}
        for role, (prop, op, label, first) in ROLES.items():
            if t < first:
                continue
            ranked = sorted(avail, key=lambda m: goodness(m, prop, op), reverse=True)
            share = max(0.12, 0.65 - 0.1 * t)
            k = max(1, math.ceil(len(ranked) * share))
            thr = max(goodness(ranked[k - 1], prop, op), last_thr.get(role, -1e9))
            thr = min(thr, goodness(ranked[0], prop, op))
            last_thr[role] = thr
            qual = [m for m in ranked if goodness(m, prop, op) >= thr]
            prev = chains[role][-1].material if chains[role] else None
            if prev in {m.name for m in qual}:
                pick = next(m for m in qual if m.name == prev)  # keep using it while it's good enough
            else:  # cheapest = earliest tier, base before alloy; ties broken by the seed
                best = min((m.tier, m.category == "alloy") for m in qual)
                pick = rng.choice([m for m in qual if (m.tier, m.category == "alloy") == best])
            part = f"{pick.name} {label}"
            if not chains[role] or chains[role][-1].part != part:
                chains[role].append(RoleStep(t, pick.name, thr if op == ">=" else -thr, part))
            cur[role] = part
        current.append(cur)
    return chains, current


# ---------------------------------------------------------- world assembly ---

COMPONENT_NAMES = [
    "Rotor", "Stator", "Circuit Board", "Motor", "Heat Exchanger", "Control Unit",
    "Pressure Valve", "Sensor Array", "Battery Cell", "Optic Module", "Field Coil",
    "Servo", "Compressor", "Processor", "Gyroscope", "Thruster", "Capacitor", "Drill Head",
    "Filter Stack", "Actuator", "Transformer", "Bearing Assembly", "Cooling Loop",
    "Signal Relay", "Power Cell", "Magnetron", "Turbine Blade", "Data Core",
]
MILESTONE_NAMES = [
    "Survey Hub", "Field Lab", "Power Grid", "Orbital Relay", "Research Station",
    "Fabrication Bay", "Signal Array", "Ore Sorter", "Deep Core Probe", "Atmo Processor",
    "Cargo Launcher", "Quantum Lab", "Data Vault", "Fusion Test Rig", "Mass Driver",
]


class _Builder:
    def __init__(self, seed: int):
        self.seed = seed
        self.items: dict[str, Item] = {}
        self.recipes: list[Recipe] = []

    def item(self, name: str, kind: str, tier: int) -> str:
        if name not in self.items:
            self.items[name] = Item(name, kind, tier)
        return name

    def recipe(self, **kw) -> Recipe:
        r = Recipe(**kw)
        self.recipes.append(r)
        return r


def generate_world(seed: int) -> World:
    names = NameGen(rng_for(seed, "names"))
    planets = gen_planets(rng_for(seed, "planets"), names)
    n_tiers = TIERS_HOME + TIERS_PER_PLANET * (len(planets) - 1)
    resources, keys = gen_resources(rng_for(seed, "resources"), names, planets)
    base = gen_materials(rng_for(seed, "materials"), resources, planets, keys)
    alloys = gen_alloys(rng_for(seed, "alloys"), base, len(planets))
    mats = base + alloys
    by_name = {m.name: m for m in mats}
    res_by_name = {r.name: r for r in resources}

    rng = rng_for(seed, "recipes")
    b = _Builder(seed)

    # needs chain: thresholds that only the key material meets
    needs: list[NeedLink] = []
    for k, rname in keys.items():
        p = planets[k]
        h = p.hazard
        key = next(m for m in base if m.source == [rname])
        earlier = [m for m in mats if m is not key and m.tier < p.start_tier]
        best = max((goodness(m, h.prop, h.op) for m in earlier), default=goodness(key, h.prop, h.op) - 10)
        thr = round((goodness(key, h.prop, h.op) + best) / 2, 1)
        part_label, gear_name = GEAR[h.tag]
        if any(n.gear == gear_name for n in needs):
            gear_name = f"{gear_name} ({p.name})"
        needs.append(NeedLink(k, h, thr if h.op == ">=" else -thr, key.name, rname,
                              planets[k - 1].index, f"{key.name} {part_label}", gear_name))

    chains, current = assign_roles(rng_for(seed, "roles"), mats, n_tiers)

    # parts (one recipe per material/role pair actually used)
    for role, steps in chains.items():
        for s in steps:
            m = by_name[s.material]
            b.item(s.part, "part", m.tier)
            b.recipe(name=s.part, kind="part", machine="Constructor",
                     inputs={m.name: rng.randint(1, 3)}, outputs={s.part: rng.choice((1, 1, 2))}, tier=m.tier)

    # tiers: components, machines, milestones
    tier_planet = [max(p.index for p in planets if p.start_tier <= t) for t in range(n_tiers)]
    comp_pool = COMPONENT_NAMES[:]
    rng.shuffle(comp_pool)
    mile_pool = MILESTONE_NAMES[:]
    rng.shuffle(mile_pool)
    comp_count: dict[str, int] = {}

    def comp_name() -> str:
        base_name = comp_pool[len(comp_count) % len(comp_pool)]
        n = sum(1 for c in comp_count if c.startswith(base_name)) + 1
        name = base_name if n == 1 else f"{base_name} Mk{n}"
        comp_count[name] = 1
        return name

    tiers: list[Tier] = []
    components_by_tier: list[list[str]] = []
    for t in range(n_tiers):
        cur = current[t]
        prev = current[t - 1] if t else {}
        fresh = [part for role, part in cur.items() if prev.get(role) != part]
        machine = "Constructor" if t == 0 else ("Assembler" if t < 3 else "Manufacturer")
        comps = []
        for _ in range(2 + (t >= 2)):
            roles = rng.sample(sorted(cur), rng.randint(2, 3))
            inputs = {cur[r]: rng.randint(1, 6) for r in roles}
            if t and rng.random() < 0.6:
                inputs[rng.choice(components_by_tier[t - 1])] = rng.randint(1, 3)
            name = b.item(comp_name(), "component", t)
            comps.append(b.recipe(name=name, kind="component", machine=machine, inputs=inputs,
                                  outputs={name: 1}, tier=t))
        for part in fresh:  # every new part must be used in its tier
            if not any(part in c.inputs for c in comps):
                rng.choice(comps).inputs[part] = rng.randint(1, 4)
        components_by_tier.append([c.name for c in comps])
        tiers.append(Tier(t, tier_planet[t], [m for m, mt in MACHINES if mt == t],
                          components_by_tier[t], ""))

    # a local specialty: each later planet's own material is needed on arrival
    for p in planets[1:]:
        t = p.start_tier
        local = [m for m in base if m.home_planet == p.index and m.tier <= t]
        if not local:
            continue
        m = rng.choice(local)
        role = max((r for r in current[t]), key=lambda r: goodness(m, ROLES[r][0], ROLES[r][1]))
        part = f"{m.name} {ROLES[role][2]}"
        if part not in b.items:
            b.item(part, "part", m.tier)
            b.recipe(name=part, kind="part", machine="Constructor", inputs={m.name: 2},
                     outputs={part: 1}, tier=m.tier)
        comp = next(r for r in b.recipes if r.name == components_by_tier[t][0])
        comp.inputs[part] = rng.randint(2, 5)

    # machine build recipes (by hand at the workbench)
    for name, mt in MACHINES:
        ref = max(0, mt - 1)
        cur = current[ref]
        inputs = {cur[r]: rng.randint(2, 10) for r in rng.sample(sorted(cur), rng.randint(2, 3))}
        if mt >= 2:
            inputs[rng.choice(components_by_tier[mt - 1])] = rng.randint(2, 5)
        b.item(name, "machine", mt)
        b.recipe(name=f"Build {name}", kind="build", machine="Workbench", inputs=inputs,
                 outputs={name: 1}, tier=mt)

    # gear for each planet's hazard
    for n in needs:
        key = by_name[n.key_material]
        t = planets[n.planet].start_tier - 1
        b.item(n.gear_part, "gear_part", key.tier)
        b.recipe(name=n.gear_part, kind="part", machine="Constructor", inputs={key.name: 4},
                 outputs={n.gear_part: 1}, tier=key.tier)
        b.item(n.gear, "gear", t)
        b.recipe(name=n.gear, kind="gear", machine="Workbench",
                 inputs={n.gear_part: 8, components_by_tier[t][-1]: 4}, outputs={n.gear: 1}, tier=t)

    # milestones; the last tier of each planet phase is the trip to the next planet
    gear_for = {planets[n.planet].start_tier - 1: n.gear for n in needs}
    for t, tier in enumerate(tiers):
        if t in gear_for:
            nxt = next(p for p in planets if p.start_tier == t + 1)
            name = f"Lander to {nxt.name}"
        elif t == n_tiers - 1:
            name = "Interstellar Gate"
        else:
            name = mile_pool.pop()
        inputs = {c: rng.randint(5, 20) * (t + 1) for c in tier.components}
        if t in gear_for:
            inputs[gear_for[t]] = 1
        tier.milestone = b.item(name, "milestone", t)
        b.recipe(name=name, kind="milestone", machine="Hub", inputs=inputs, outputs={name: 1}, tier=t)

    # materials: alloys and processing, then prune what nothing uses
    used = {i for r in b.recipes for i in r.inputs}
    changed = True
    alloy_inputs: set[str] = set()
    while changed:
        changed = False
        live_alloys = [a for a in alloys if a.name in used]
        alloy_inputs = {s for a in live_alloys for s in a.source}
        for m in mats:
            if m.name not in used and m.name in alloy_inputs:
                used.add(m.name)
                changed = True
    live = [m for m in mats if m.name in used]
    for m in live:
        b.item(m.name, "material", m.tier)
        if m.category == "alloy":
            a, c = m.source
            b.recipe(name=m.name, kind="alloy", machine="Foundry", inputs={a: 2, c: 1},
                     outputs={m.name: 2}, tier=m.tier)
        else:
            r = res_by_name[m.source[0]]
            wash = r.category == "metal_ore" and rng.random() < 0.5
            inputs = {r.name: rng.choice((1, 2, 2, 3))}
            if wash:
                inputs["Water"] = 1
            b.recipe(name=m.name, kind="process", machine=PROCESSOR[r.category], inputs=inputs,
                     outputs={m.name: 1}, tier=m.tier, needs_water=wash)

    # byproducts: either a free extra source of another raw, or waste to deal with
    live_res = {i for r in b.recipes for i in r.inputs if i in res_by_name}
    key_res = set(keys.values())
    for r in [r for r in b.recipes if r.kind == "process"]:
        if rng.random() >= 0.35:
            continue
        own = next(i for i in r.inputs if i != "Water")
        cands = [x for x in sorted(live_res) if x not in key_res and x != own and x != "Water"
                 and res_by_name[x].tier <= r.tier]
        if cands and rng.random() < 0.5:
            r.outputs[rng.choice(cands)] = 1
        else:
            waste = b.item(f"{res_by_name[own].root} Slag", "waste", r.tier)
            r.outputs[waste] = 1

    # a catalyst loop: a component consumes the catalyst and returns it spent
    cat_steps = [s for s in chains["catalyst"] if s.tier >= 2]
    if cat_steps and n_tiers > 2:
        cat_part = current[2]["catalyst"]
        comp = next(r for r in b.recipes if r.name == components_by_tier[2][0])
        spent = b.item(f"Spent {cat_part}", "waste", 2)
        comp.inputs[cat_part] = 1
        comp.outputs[spent] = 1
        filler = min((m for m in live if m.tier <= 2 and m.category != "alloy"), key=lambda m: m.tier)
        b.recipe(name=f"Regenerate {cat_part}", kind="regen", machine="Refinery",
                 inputs={spent: 1, filler.name: 1}, outputs={cat_part: 1}, tier=2)

    # extraction for every raw resource still in use
    live_res = {i for r in b.recipes for i in r.inputs if i in res_by_name}
    resources = [r for r in resources if r.name in live_res]
    extract = []
    for r in resources:
        b.item(r.name, "raw", r.tier)
        extract.append(Recipe(name=f"Extract {r.name}", kind="extract", machine=r.extractor,
                              inputs={}, outputs={r.name: 1}, tier=r.tier, planets=list(r.planets)))
    b.recipes = extract + b.recipes

    # machines nothing runs on are dropped
    used_machines = {r.machine for r in b.recipes}
    for name, _ in MACHINES:
        if name not in used_machines:
            del b.items[name]
            b.recipes = [r for r in b.recipes if r.name != f"Build {name}"]
    for tier in tiers:
        tier.machines = [m for m in tier.machines if m in used_machines]

    return World(seed, names.root(5, 8) + " System", planets, resources, live, b.items,
                 b.recipes, {k: v for k, v in chains.items() if v}, tiers, needs)


# ----------------------------------------------------- planet variants ---


def planet_variants(world: World, planet: Planet) -> list[str]:
    """Local recipe variants and rule changes on one planet (D08 sketch)."""
    tags = {h.tag for h in planet.traits}
    local_liquids = [r for r in world.resources if planet.index in r.planets and r.category == "liquid"]
    out = []
    for r in world.recipes:
        if r.needs_water and "no_water" in tags:
            ore = next(i for i in r.inputs if i != "Water")
            if local_liquids:
                out.append(f"{r.name}: washed with {local_liquids[0].name} instead of Water")
            else:
                out.append(f"{r.name}: dry process, {ore} x{r.inputs[ore] * 2}, no Water, half speed")
    if "high_gravity" in tags:
        out.append("All machine builds cost +50% parts (heavier foundations)")
    if "corrosive" in tags:
        out.append("All machine builds also need 2 Seals; exposed machines wear out")
    if "extreme_cold" in tags and planet.water:
        out.append("Water is ice: Water Extractors need heating (extra power)")
    if "long_night" in tags:
        out.append("Solar output 0 for half of each day: storage or non-solar power required")
    if "low_gravity" in tags:
        out.append("Landers and launches cost -40%")
    if planet.kind == "gas_giant":
        out.append("No surface: only Orbital Harvesters and station modules can be built")
    return out
