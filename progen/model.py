"""Data model of a generated world. Plain dataclasses, no logic."""

from __future__ import annotations

from dataclasses import dataclass, field

PROPERTIES = (
    "strength",
    "density",
    "conductivity",
    "heat_resistance",
    "reactivity",
    "transparency",
)

# Machines are fixed types (candidate answer to D10); only their recipes are generated.
MACHINES = (
    ("Miner", 0),
    ("Water Extractor", 0),
    ("Smelter", 0),
    ("Constructor", 0),
    ("Assembler", 1),
    ("Pump", 1),
    ("Refinery", 1),
    ("Foundry", 2),
    ("Deep Drill", 2),
    ("Manufacturer", 3),
    ("Orbital Harvester", 4),
)
MACHINE_TIER = dict(MACHINES)
# "Machines" that are always available: hand crafting and the milestone hub.
HAND = ("Workbench", "Hub")


@dataclass
class Hazard:
    tag: str
    description: str
    prop: str | None = None  # property the counter-gear must have
    op: str | None = None  # ">=" or "<="


@dataclass
class Planet:
    index: int
    name: str
    kind: str
    temperature_c: int
    gravity_g: float
    atmosphere: str
    water: bool
    day_hours: float
    traits: list[Hazard] = field(default_factory=list)
    hazard: Hazard | None = None  # the one that drives the needs chain
    start_tier: int = 0


@dataclass
class Resource:
    name: str
    root: str
    category: str
    planets: list[int]
    extractor: str
    deep: bool = False
    tier: int = 0


@dataclass
class Material:
    name: str
    root: str
    category: str  # metal, ceramic, glass, polymer, resin, fiber, alloy
    props: dict[str, float]
    source: list[str]  # one resource, or two materials for an alloy
    tier: int = 0
    home_planet: int = 0  # planet where its resource is first found


@dataclass
class Item:
    name: str
    kind: str  # raw, material, part, component, machine, milestone, gear_part, gear, waste
    tier: int


@dataclass
class Recipe:
    name: str
    kind: str  # extract, process, alloy, part, build, component, milestone, gear, regen
    machine: str
    inputs: dict[str, int]
    outputs: dict[str, int]
    tier: int
    planets: list[int] | None = None  # extraction: only on these planets
    needs_water: bool = False


@dataclass
class RoleStep:
    tier: int
    material: str
    threshold: float
    part: str


@dataclass
class NeedLink:
    planet: int
    hazard: Hazard
    threshold: float
    key_material: str
    key_resource: str
    source_planet: int
    gear_part: str
    gear: str


@dataclass
class Tier:
    index: int
    planet: int
    machines: list[str]
    components: list[str]
    milestone: str


@dataclass
class World:
    seed: int
    system_name: str
    planets: list[Planet]
    resources: list[Resource]
    materials: list[Material]
    items: dict[str, Item]
    recipes: list[Recipe]
    roles: dict[str, list[RoleStep]]
    tiers: list[Tier]
    needs: list[NeedLink]

    def planet_of_tier(self, t: int) -> int:
        return self.tiers[t].planet

    def material(self, name: str) -> Material:
        return next(m for m in self.materials if m.name == name)
