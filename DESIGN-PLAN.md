# Design Plan

The order in which we design the game, the rules for changing decisions, and the status of every
decision. `DESIGN.md` holds the ideas and the vision; this file holds the **process** and the
**decisions**.

Tool: `python tools/plan.py` reads the table below (`check`, `next`, `impact D03`, `stale D03`).
CI runs `check`, so the table can't silently break the rules.

---

## 1. Base rules

### Process rules

- **P1. Decide in order.** Every decision lists the decisions it depends on. It can only be
  **locked** when everything it depends on is locked. Dependencies always point to earlier IDs, so
  the table order is a valid design order.
- **P2. The change rule.** Changing a locked decision makes **every decision that depends on it,
  directly or indirectly, `stale`**. Stale decisions must be reviewed before any *other* decision
  is locked. (`python tools/plan.py stale D03` marks them.)
  - Reviewing is not always rewriting: often the answer is "still fine", and it goes straight back
    to locked. But someone has to look.
  - This is finer than "redo everything after it": changing D03 only invalidates what actually
    builds on D03, not unrelated later decisions. `tools/plan.py impact D03` shows the list before
    you commit to the change.
- **P3. Draft ahead freely.** Ideas for later decisions can be written down any time (status
  `draft`). Drafts are not binding and don't block anything.
- **P4. Prototype before locking** where possible. D06–D14 (progression) are tested with the
  generator (milestone 0) before they are locked.
- **P5. Log every change** to a locked decision in the change log (section 4): what changed, why,
  and which decisions went stale.
- **P6. Parking lot.** New feature ideas that don't serve a pillar (D01) go to the parking lot
  (section 5), not into the design.

### Statuses

| Status | Meaning |
|---|---|
| `open` | Not decided yet. Questions listed. |
| `draft` | A proposed answer exists (often from `DESIGN.md`), not final. |
| `locked` | Decided. Everything later may build on it. |
| `stale` | Was locked or drafted, but something it depends on changed. Review before continuing. |

### Design rules (apply to every decision)

- **R1. No oatmeal.** A generated thing only counts as content if it changes the player's
  decisions. Numeric or cosmetic variety alone doesn't count.
- **R2. Deterministic.** Everything generated comes from the seed. Same seed + same version = same
  world, on every machine.
- **R3. Simulation separate from presentation.** Game rules never live in rendering/UI code.
- **R4. Playable milestones.** Every milestone ends with something playable or testable.
- **R5. One person can build it.** Prefer designs that are generated or systemic over designs
  that need lots of handmade content.
- **R6. Art comes from systems, not from an artist.** The developer is an engineer, not an
  artist: precise CAD-style modelling, not freehand. So looks are generated from parameters
  (terrain, colours, biomes, material appearance) or built as clean, precise, geometric models
  (machines, parts, buildings). Choose a style where precision and consistency *are* the beauty,
  never one that needs hand-painted or organic hand-sculpted assets.
- **R7. Plausible physics.** The world follows real physics where it can, then simplifies.
  Planet temperature comes from the star and the orbit distance (farther = colder), gravity from
  mass and radius, travel between planets takes time based on distance. Game time may run faster
  than real time, but the relationships stay physical. Generated parameters are *derived*, not
  rolled independently.
- **R8. Runs on modest hardware.** A low-spec setting that drops graphics hard but keeps the game
  playable is part of the design, not an afterthought. Dev targets: the laptop (Iris Plus
  graphics) at lowest settings, the desktop (Quadro K4000, i7, 32 GB DDR3) as the normal test PC.

---

## 2. Decision table

| ID | Decision | Depends on | Status |
|---|---|---|---|
| D01 | Pillars and player fantasy | - | locked |
| D02 | Core loop (minute / hour / planet) | D01 | locked |
| D03 | Pressure: danger, survival, combat or none | D01, D02 | locked |
| D04 | Scale and pacing targets | D01, D02 | locked |
| D05 | World structure | D01, D04 | draft |
| D06 | Materials and property model | D01 | draft |
| D07 | Resources and their distribution | D05, D06 | open |
| D08 | Planet parameters and constraints | D03, D05, D06 | draft |
| D09 | Recipe / tech graph rules | D02, D04, D06, D07 | draft |
| D10 | Machines and property requirements | D06, D09 | draft |
| D11 | Research and discovery mechanic | D02, D06, D09 | open |
| D12 | Goals: needs chains | D03, D08, D09, D10 | draft |
| D13 | Carry-over: global vs planet layer | D04, D09, D11, D12 | open |
| D14 | Generator validation and playtime metrics | D04, D09, D12 | draft |
| D15 | Player abilities and tools | D02, D03, D08 | open |
| D16 | Travel between planets and systems | D05, D12, D13, D15 | open |
| D17 | Building and terrain | D02, D15 | open |
| D18 | Logistics | D09, D16, D17 | open |
| D19 | Power and energy | D08, D09, D18 | open |
| D20 | Simulation model | D18, D19 | draft |
| D21 | Multiplayer model | D20 | draft |
| D22 | Engine and language | D20, D21 | open |
| D23 | Planet rendering, terrain tech, large worlds | D05, D17, D22 | open |
| D24 | Save format and determinism rules | D20, D21, D22 | open |
| D25 | Art direction and generated visuals | D01, D08, D22 | open |
| D26 | UI / UX | D09, D11, D17 | open |
| D27 | Audio | D25 | open |
| D28 | Title and identity | D01, D25 | open |

Phases: **A Foundation** D01–D05 · **B Progression** D06–D14 (milestone 0) ·
**C Game systems** D15–D21 · **D Technology** D22–D24 · **E Presentation** D25–D28.

---

## 3. Decisions

Each entry: the question, the current answer (if any), what still has to be answered, and when it
can be locked.

### Phase A: Foundation

#### D01. Pillars and player fantasy
- **Question:** What is the game *about*, in 3–5 pillars every later decision is checked against?
- **Decision (locked 2026-11-14).** Pillars, ranked: when two conflict, the higher one wins.
  1. **Every planet is a puzzle.** Progression is generated, not only terrain. Planets bring new
     decisions, not just bigger numbers. Parts may repeat from earlier planets (known materials,
     familiar chains), but the mix and the constraints are new. Planets also *look* different,
     because their look comes from the same parameters as their constraints (see R6).
     *Rejects:* a hand-made tech tree; planets that are reskins.
  2. **Optimizing is the core activity.** Most time goes into designing, connecting and improving
     factories; exploring, travel and research feed into it. The demands grow with distance from
     the start: later planets need far bigger output (orders of magnitude, numbers set in D04).
     *Rejects:* long side activities unrelated to the factory.
  3. **Discover by doing.** Materials, properties and planets are learned through play (scanning,
     testing, building), never handed over as a wiki. You never quite know what you'll be doing
     next. *Rejects:* a full encyclopedia from the start; research as a pure progress bar.
  4. **Growing scale.** From one base to a network across a system, and later across systems.
     *Rejects:* resetting the player between planets with nothing carried over.
- **Not pillars:** combat, story, survival. Allowed only if they serve a pillar (decided in D03).
- **Player fantasy:** *"You're a pioneer engineer sent to make a star system self-sufficient: one
  planet at a time, each one a problem nobody has solved before."* A light frame, no scripted
  story; the needs chain provides the goals.

#### D02. Core loop
- **Question:** What does the player do minute to minute, hour to hour, planet to planet?
- **Decision (locked 2026-11-14):**
  - **Minute:** walk/fly, scan and mine, place machines, connect belts and pipes, watch it run,
    find the bottleneck, fix it. Must be quick and easy to understand.
  - **Tutorial:** short and fully skippable *without affecting the game*. The player lands,
    builds the main hub, then enters a **VR training simulation** inside the hub where the
    tutorial happens. Done or skipped, they return to the real world at the same starting point
    with the same resources (like Satisfactory giving you the starter items when you skip).
  - **Hour (one tier):** a new need → find/test a fitting material → build a new production
    line → milestone → unlock. Reward: the factory visibly grows. A tier can take longer than an
    hour, depending on how much the player optimizes.
  - **Planet:** arrive *almost* from scratch (sometimes with more, see D13) → survey resources
    and hazards → bootstrap → scale up → reach the planet's goals → connect it to the network →
    leave; the base keeps running.
  - **Goals are varied, not only "make N of X"**: e.g. produce a power output, sustain a rate,
    build a structure, export a stream to the network. Goals must give exploring a reason (find,
    survey, discover), otherwise exploring a planet feels pointless. Details in D12.
  - **System:** planets feed each other, but not all: some planets are autonomous, others
    depend on imports.
  - **Going back:** a new planet regularly needs more of something from an old one, so old
    factories get expanded; a base is never really "done".
  - **Time split:** mostly building and optimizing, a good share exploring and discovering, a
    smaller part travel and logistics.

#### D03. Pressure
- **Question:** Is there danger (hostile environment, creatures, combat), survival meters, or
  pure building?
- **Decision (locked 2026-11-14): the planet is the enemy.**
  - **No creatures, no combat** (hard to generate, hard to animate, heavy on weak PCs). Parked.
  - **The player can die** from the environment: heat, cold, toxic air, radiation, pressure,
    lack of oxygen. Suits and gear raise the limits; different planets need different materials
    for surviving as well as for building.
  - **Oxygen level varies per planet** and affects the player even where it's breathable: low
    oxygen slows you down; high oxygen boosts you. (R7: might also raise fire risk; see D08.)
  - **Death is mild:** respawn at the hub, go back for the dropped backpack.
  - **No hunger or thirst** in the normal game (parked for an ultra-hardcore mode).
  - **Machines never break on their own.** Only weather damages them, and only when they stand
    outside: a machine inside a building is safe. Walls and buildings themselves are not damaged.
    So weather pushes the player to enclose factories, but the enclosure isn't a chore.
  - **Weather and events come from the planet type** and can be planned for (forecast, seasons,
    long nights), no random punishment. Examples: sandstorms on desert planets, ice falling on
    ice planets, giant waves on ocean planets (per R7, from tides of a close moon or giant).
  - **Weather damages, never destroys:** a damaged machine is repaired (D17 decides how).

#### D04. Scale and pacing targets
- **Decision (locked 2026-11-14).** Numbers are rough sizes to tune, never commitments.
  - Rough sizes from DESIGN.md stay as orientation: home planet 150+ h, later planets 30–80 h,
    thousands of hours in the home system.
  - **A planet's length comes from its content**, not from a target: its size, number of
    resources, number and kind of goals, its role (autonomous or import-dependent), plus the
    research needed to travel onward (interplanetary, later interstellar). Later planets aren't
    automatically longer, but can be because they're bigger.
  - **Demand grows with distance by orders of magnitude** (pillar 2); better tools grow with
    it, so later planets need far bigger output without taking proportionally longer.
  - Short tutorial; the first automation comes in the first session. Each tier should be
    reachable in one or a few evening sessions, so a session ends with something visible.
  - **First trip to space only after substantial progress** on the home planet, not early.
  - **Time scale:** an Earth-like day lasts roughly one to two real hours; other planets' days
    scale with their rotation (R7).
  - **Travel takes in-game time** (e.g. days between planets, varying with planet positions).
    The player can stay aboard and spend it (walk around the ship, pre-research the destination)
    or skip it: the time passes in the world, but the player doesn't wait. Details in D16;
    skipping means remote bases fast-forward as rates (D20); co-op needs a rule for it (D21).

#### D05. World structure
- **Draft** (DESIGN.md §5): galaxy → systems → planets/moons, all from one seed, generated near
  the player. Start on an Earth-like planet in the home system.
- **Open:** Real-scale or compressed planets (Astroneer-small vs huge)? How many planets per
  system? Moons, asteroid belts, gas giants (stations only)? Is the starting planet always
  Earth-like? Per R7, planet parameters follow from star type and orbit (the prototype still
  rolls temperature per planet kind; update it once D05/D08 are decided).
- **Lock when:** the hierarchy and rough sizes are fixed.

### Phase B: Progression (tested by the generator, milestone 0)

#### D06. Materials and property model
- **Draft:** materials have numeric properties (strength, density, conductivity, heat
  resistance, reactivity, transparency, radioactivity…). Parts and machines require property
  thresholds. Alloys/composites combine materials.
- **Open:** Final property list (5–8; each one must drive decisions). Can the player *see* all
  properties at once or discover them? Are there property trade-offs (strong but heavy)?
- **Lock when:** the generator shows that different seeds pick different key materials.

#### D07. Resources and distribution
- **Open:** Which resource categories exist (ores, crystals, gases, liquids, organics)? How
  does geology decide what is where (planet type → resource categories)? Is each resource finite
  per node or infinite (Satisfactory nodes)? How many raw resources per planet (5–10?)?
- **Lock when:** distribution rules produce "this resource is only on the moon" situations
  regularly, but never an unwinnable world.

#### D08. Planet parameters and constraints
- **Draft** (DESIGN.md §4.3): temperature, gravity, atmosphere, water, day length, geology.
  Constraints change the factory (no water → no water cooling, long night → no solar alone…).
- **Open:** Full parameter list; which constraints affect the player vs only machines (D03);
  how many constraints per planet (2–3 strong ones beat 10 weak ones).
- **Input from D03:** add oxygen level (player speed/stamina, maybe fire risk) and weather
  (type, strength, frequency, forecast) to the planet parameters. Weather damages only exposed
  machines.
- **Lock when:** every constraint has a mechanical effect, written down.

#### D09. Recipe / tech graph rules
- **Draft:** generated per world; tiers; byproducts; some loops (catalysts); no dead ends; early
  items reachable with starting tools.
- **Open:** Graph size per planet; how much of the graph is world-wide vs planet-local; how many
  alternative recipes; how byproducts are handled (must be used or disposed of?).
- **Lock when:** the generator produces valid graphs for 1000 seeds and two seeds look different
  (D14 metrics).

#### D10. Machines and property requirements
- **Draft:** machines are built from parts; parts have property requirements, so the material
  used differs per world.
- **Open:** Fixed list of machine *types* (smelter, assembler, refinery…) with generated recipes,
  or generated machine types too? (Fixed types are much easier to model and animate in 3D;
  strong candidate.) Do machines wear out (D03, D08)?

#### D11. Research and discovery mechanic
- **Open:** How does the player learn a material's properties: scanner, lab tests, trial and
  error, building test pieces? Is research a separate activity or part of the factory (feed
  samples to a lab)? Without this, "materials with properties" is just a spreadsheet.

#### D12. Goals: needs chains
- **Draft** (DESIGN.md §4.4): problems instead of quests: next planet is cold → suits fail →
  need a material with property Y → only on planet Z → …
- **Open:** Is there an end goal per system (build something big), or only the chain? Optional
  side goals? How is the next need shown to the player?
- **Input from D02:** goal *types* must vary (output amount, power output, sustained rate,
  structure, export stream to the network…) and must give exploration a purpose.

#### D13. Carry-over
- **Open:** What carries over between planets: knowledge of materials? Blueprints? Machine
  tiers? Proposal (DESIGN.md §4.5): global = knowledge, blueprints, transport tech; local =
  resources, constraints, recipe variants. Risk: too much carry-over → copy-paste the old base;
  too little → frustrating restart.
- **Input from D02:** arrival is *almost* from scratch; sometimes the player brings more.

#### D14. Generator validation and playtime metrics
- **Draft** (DESIGN.md §10): every world completable (reachability, no dead ends); playtime
  estimate per planet; "two seeds feel different" metric.
- **Open:** How to measure "feels different": key materials per role, bottleneck resources,
  planet order, graph shape? How to calibrate the playtime estimate (later: against real play)?

### Phase C: Game systems

#### D15. Player abilities and tools
- **Open:** Movement (jetpack? vehicles?), mining tool, scanner, suit upgrades, inventory size,
  hand crafting vs machines only.
- **Input from D03:** the suit is the player's survival system (temperature, air, radiation
  limits); oxygen level changes movement.

#### D16. Travel between planets and systems
- **Open:** Rockets built in the factory? Launch pads? Ships the player flies? Cutscene travel?
  Cost of travel tied to gravity (D08). Per R7, travel takes time based on distance; how game
  time relates to real time (and what the player does meanwhile) is decided here.
- **Input from D04:** trips take in-game days; the player can live through them aboard (walk
  the ship, pre-research the destination) or skip them; travel time depends on where the
  planets are in their orbits.

#### D17. Building and terrain
- **Open:** Grid / snapping / free placement; foundations; deformable terrain (Astroneer) or not;
  blueprints (copy/paste) and how they interact with D13.

#### D18. Logistics
- **Open:** Belts, pipes, trains, drones, vehicles; interplanetary transport (rockets on a
  schedule, space elevators); what's automatic vs player-driven.

#### D19. Power and energy
- **Open:** Power sources per planet type (solar, wind, geothermal, fuel, nuclear…), storage,
  and how planet constraints change them.

#### D20. Simulation model
- **Draft** (DESIGN.md §6): full simulation near the player, rate-based ("12/min") elsewhere;
  core separate from rendering, headless mode.
- **Open:** How to switch between detailed and rate mode without exploits; tick rate.

#### D21. Multiplayer model
- **Draft** (DESIGN.md §7): singleplayer first, co-op later; host-authoritative; clients
  generate the world from the seed, only changes are sent.

### Phase D: Technology

#### D22. Engine and language
- **Open:** Godot 4 (favourite; double precision builds, C# or GDScript, good on Linux) vs Unity
  / Unreal. Where the simulation core lives (C#? Rust/C++ via GDExtension?). Hardware per R8:
  check that the Quadro K4000 (Kepler, old driver branch) runs Godot 4's Vulkan renderer; the
  OpenGL "Compatibility" renderer is the fallback and a candidate for the low-spec setting.

#### D23. Planet rendering, terrain tech, large worlds
- **Open:** Cube-sphere heightmap vs voxel/SDF; LOD; streaming; floating origin / doubles.

#### D24. Save format and determinism rules
- **Open:** Save = seed + diff; versioning (what happens to a world when the generator changes:
  pin the generator version per save?).

### Phase E: Presentation

#### D25. Art direction and generated visuals
- **Open:** Style within R6: e.g. clean "CAD / technical" look for machines, generated
  low-poly or stylized terrain; how biomes, materials and machines get their look from generated
  data. Landscapes should differ per planet (D01 pillar 1), driven by planet parameters.

#### D26. UI / UX
- **Open:** Build menu, recipe browser for a recipe set the player has never seen, research
  UI, map, how needs chains are shown.

#### D27. Audio
- **Open:** Music, ambience per planet type, machine sounds.

#### D28. Title and identity
- **Open:** Working title, logo, tone.

---

## 4. Change log

| Date | Decision | Change | Why | Went stale |
|---|---|---|---|---|
| 2026-11-14 | - | Plan created | - | - |
| 2026-11-14 | D01 | Locked: 4 ranked pillars, player fantasy; added rule R6 (art from systems) | First decision | - |
| 2026-11-14 | D02 | Locked: minute/hour/planet/system loops, skippable VR tutorial, varied goals; added R7 (plausible physics), R8 (modest hardware) | - | - |
| 2026-11-14 | D03 | Locked: environment is the enemy, no combat, player can die, oxygen levels, weather damages exposed machines only | - | - |
| 2026-11-14 | D03 | Added: weather damages but never destroys; machines get repaired | Answered open point | none (D04+ not locked yet) |
| 2026-11-14 | D04 | Locked: length from content, demand grows with distance, space after real progress, 1–2 h days, skippable travel | - | - |

## 5. Parking lot

Ideas that don't belong to a decision yet.

- **An MCP server in the game**: Claude (or any MCP client) can read the factory state and
  maybe act in it. Cheap to add later because the simulation is headless (R3). Fun for testing
  and debugging too.
- **Creatures and combat**: maybe later. Hard to generate procedurally and heavy on weak PCs.
- **Hardcore mode**: one death and the world is lost.
- **Ultra-hardcore mode**: hunger and thirst on top of hardcore. Suits/tech extend how long you
  last (e.g. from half an hour to hours), but only temporarily.

## 6. Planned slices (small playable prototypes)

Each tests one part of the game on its own, before anything is combined.

1. **Generator** (done as a CLI): procedural progression, `gen`.
2. **Flat factory world:** a flat map with machines, belts and generated recipes. Is building
   and optimizing fun?
3. **Planet viewer:** fly around a generated star system and look at the planets up close. Do
   planets look different and interesting (R6, R7)?
