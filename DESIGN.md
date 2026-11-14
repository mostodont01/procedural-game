# Procedural Factory Game: Design Notes

Working title: none yet. Status: idea / design phase (started 2026-11-14).

A 3D first-person factory and exploration game (in the spirit of Satisfactory + Astroneer)
set in one endless procedurally generated galaxy, where **not only the terrain but the
progression itself is procedural**: resources, materials, recipes, the tech tree and the
goals differ from world to world and from planet to planet.

---

## 1. Vision

- **One endless world.** A galaxy (a quarter of the Milky Way, maybe the whole thing): thousands of star
  systems, each with several planets and moons. Practically unlimited playtime; the realistic target is
  that the **starting solar system alone holds thousands of hours**.
- **Deep planets.** Each planet is worth **30–80 hours** of play. The starting planet
  (e.g. an Earth-like world) is the tutorial and the foundation: **150+ hours**.
- **Endless optimizing**, like Satisfactory, but the problems to optimize keep changing because every
  planet has different resources, constraints and recipes.
- **Procedural progression** so the game never turns into "same thing again on a new map".
- 3D, first-person, building on the planet surface (Satisfactory feel, Astroneer scale).
- **Singleplayer first, co-op multiplayer possible** (architecture must allow it from day one).

The galaxy size doesn't have to match No Man's Sky. Seeded generation makes size nearly free,
so it's a tuning value, not a design goal.

## 2. What I like / dislike in the reference games

| Game | Like | Dislike |
|---|---|---|
| Satisfactory | Endless optimizing of factories | Map is always the same; can get boring; map can feel small |
| Astroneer | Bigger world, more interesting gameplay, multiple planets | Repetitive: ~5 biomes on every planet, you do the same things everywhere |
| Factorio | (not played) | |

**Design consequences:**
- Maps must be generated, large, and **planets must differ in kind, not just in color**.
- No fixed set of biomes reused everywhere: biomes come from planet parameters (temperature,
  atmosphere, gravity, water, geology), so new combinations appear.
- Each planet must give **new decisions**, not only bigger numbers.

## 3. Core design rule: avoid "10,000 bowls of oatmeal"

Procedural variety that is only numeric or cosmetic feels the same after a few hours (the classic
No Man's Sky criticism). Rule for every generated system:

> A generated thing only counts as content if it **changes the player's decisions**.

## 4. Procedural progression: the core idea

### 4.1 Generated tech tree / recipe graph
- Recipes are **generated per world** (and partly per planet) from rules, not hand-written.
- Different raw resources, intermediate products and chains every world. Iron is not always
  the early metal; a key part may need a byproduct you'd normally throw away.
- Generator constraints keep it playable: chain depth, branching, byproducts, loops,
  no dead ends, early items reachable with starting tools, etc.
- Can't be solved from a wiki: each world is a new logistics puzzle.

### 4.2 Materials with properties
- Materials have **properties** (conductivity, heat resistance, density, strength, reactivity,
  radioactivity, …) instead of being just names.
- Machines and parts **require properties** ("reactor wall: heat resistance > 800 °C"),
  so which material fits differs per world/planet.
- **Discovery as gameplay:** unknown ores must be found, analyzed and tested to learn their
  properties. Research is something you *do*, not just a progress bar.

### 4.3 Planets as constraints
Planet parameters force different factory designs, e.g.:
- No water → different cooling and power generation.
- Very long nights → solar alone fails, need energy storage or other power.
- Low/high gravity → cheap/expensive launches; some machines behave differently.
- Toxic / corrosive atmosphere → wear and maintenance, sealed factories.
- Extreme cold/heat → special materials for suits, buildings, machines.
- Key resource only on a hostile moon → interplanetary logistics.

### 4.4 Goals from needs, not quest lists
Don't generate "deliver 500 of X". Generate **problems**, and tasks fall out of them:
> The next planet is at −200 °C → suits fail → need a material with property Y → only found
> on the gas giant in this system → need a ship / station that can harvest it → …

That chain of needs **is** the quest line and differs per world.

### 4.5 Two layers of progression (my proposal, to discuss)
- **Global layer:** knowledge, blueprints, ship/transport tech that carry over between planets.
- **Planet layer:** each planet's local resources, constraints and recipe variants, so arriving on a new
  planet means re-learning and re-designing, not copy-pasting the old base.

## 5. World structure

- Galaxy → star systems → planets / moons. Everything from a seed; generated only near the player.
- Start: an Earth-like planet in the home system (150+ h), then other planets in the system,
  then other systems.
- Interplanetary logistics between your bases is part of the late game.

## 6. Simulation

- Factories on planets you're not on are simulated as **rates** ("12/min"), not individual items
  on belts. Only the area around the player is simulated in full detail.
- The simulation core is kept separate from rendering/UI: easier to test, enables a headless
  mode, and is required for multiplayer.

## 7. Multiplayer

- Singleplayer is the main mode; co-op with a friend is a goal.
- So from the start: **simulation separate from presentation**, deterministic generation from seeds
  (clients generate the world themselves, only changes are sent), host-authoritative simulation.
  Adding multiplayer later to a game not designed for it is extremely painful.

## 8. Technology (open)

- 3D first-person, huge worlds. Candidates:
  - **Godot 4** (open source, good on Linux, C# or GDScript, supports double-precision builds
    for large worlds). Current favourite.
  - Unity / Unreal: more mature for large 3D, but heavier and not open source.
- Large worlds need floating-origin and/or double precision (float32 breaks down far from the origin).
- Planet terrain: probably voxel / SDF or cube-sphere heightmaps with LOD; Astroneer-style
  deformable terrain is a possible feature, not decided.
- The progression generator is pure logic: can be prototyped in Python first, ported later.

## 9. Hard problems / risks

1. **The progression generator** is the core and the least solved problem in the genre.
   If it doesn't produce interesting, different trees, the whole idea fails. So test it first.
2. **3D art, building feel and polish** at Satisfactory level: the biggest effort for one person.
3. Planet-scale terrain + LOD + streaming.
4. Simulation performance with many factories on many planets.
5. Scope: this is a multi-year project; milestones must each produce something playable or testable.

## 10. Milestone 0: progression generator prototype (next step)

A **headless Python CLI**, no game:

```
gen world --seed 42            # print resources, materials, recipes for a world
gen planet --seed 42 --planet 3  # planet constraints + local recipe variants
gen graph --seed 42 -o tree.svg  # draw the recipe / tech graph
```

Generates:
- Raw resources and their distribution across planets in a system.
- Materials with properties.
- Machines / parts with property requirements.
- The recipe graph (DAG with byproducts and some loops).
- Planet constraints and the "needs chain" that drives progression.

**Success criteria:**
- Two different seeds give trees that *feel* different (different bottlenecks, different
  key materials, different order of play), not just renamed items.
- Every generated tree is completable (automatic checks: reachability, no dead ends).
- Rough playtime estimate per planet from the tree size is in the 30–80 h range.

Tests + CI like my other projects.

### First prototype (2026-11-14): `progen/`, see README

What it does: planets with hazards → resources per planet → materials with 6 properties →
part roles whose property requirement rises each tier ("wire: conductivity ≥ X") → fixed machine
types with generated recipes → components and milestones per tier → a needs chain where each
planet's hazard can only be solved by one key material from the previous planet.

First findings:
- 1000/1000 seeds valid (reachable, no dead ends, needs chain unique).
- Rising property requirements are what make part materials change over the game; they also
  decide which material is "the metal" (first plates: metal ~70%, ceramic ~30%, glass a few %).
- A "use the weakest material that qualifies" rule biased everything toward ceramics: a
  selection rule can create its own sameness. Watch for this in every rule.
- Alloys only matter in ~50% of worlds; some roles (e.g. wire) keep one material all game.
  Both are tuning questions for D06/D09.
- Needs chains read like a story ("Fuhouk is corrosive → Corrosion Suit needs an inert liner →
  only Grougryxol Resin, found on Tiopox"). Still one hazard per planet; richer chains later.
- The playtime estimate is a placeholder tuned to the targets; it only compares seeds/planets.

## 11. Open questions

- Working title.
- Exactly what carries over between planets vs. what is relearned.
- Is there any danger / combat / survival pressure, or pure building and exploring?
- How the player travels between planets and systems (ships, launch sites, teleport tech?).
- Deformable terrain (Astroneer) or not.
- Engine: confirm Godot after the generator prototype.
