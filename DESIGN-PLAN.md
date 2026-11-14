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

---

## 2. Decision table

| ID | Decision | Depends on | Status |
|---|---|---|---|
| D01 | Pillars and player fantasy | - | draft |
| D02 | Core loop (minute / hour / planet) | D01 | open |
| D03 | Pressure: danger, survival, combat or none | D01, D02 | open |
| D04 | Scale and pacing targets | D01, D02 | draft |
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
- **Draft** (from DESIGN.md §1–3):
  1. *Endless optimizing* of factories, where the problem keeps changing.
  2. *Every world and planet is a new puzzle*: procedural progression, not just procedural terrain.
  3. *Discovery*: unknown materials, unknown planets, learning by doing.
  4. *Scale*: from one Earth-like planet to a whole system and beyond.
- **Open:** Is "discovery" equal to "optimizing", or secondary? What's the one-sentence fantasy
  ("a stranded engineer…", "a corporate surveyor…", no story at all)?
- **Lock when:** pillars are short enough to reject an idea with.

#### D02. Core loop
- **Question:** What does the player do minute to minute, hour to hour, planet to planet?
- **Open:** Rough sketch to confirm:
  - *Minute:* explore, mine/scan, build and connect machines, fix bottlenecks.
  - *Hour:* reach a new tier: new material, new machine, rebuild part of the factory.
  - *Planet:* arrive, survey, learn local materials/constraints, bootstrap, solve the planet's
    needs, connect it to the network, leave.
- Where does the player spend most time: walking/exploring vs building vs planning?
- **Lock when:** the three loops are written and each has a clear "reward".

#### D03. Pressure
- **Question:** Is there danger (hostile environment, creatures, combat), survival meters, or
  pure building?
- **Open:** Options: (a) none, pure sandbox; (b) environmental only (temperature, atmosphere,
  radiation, storms: the planet is the enemy); (c) creatures/combat. Option (b) fits "planets
  as constraints" without the cost of AI and combat; strong candidate.
- **Affects:** planet constraints, player tools, needs chains (a cold planet only matters if cold
  can hurt you or your machines).
- **Lock when:** chosen, with the list of what can fail (player, machines, both).

#### D04. Scale and pacing targets
- **Draft:** 150+ h on the starting planet, 30–80 h per later planet, thousands of hours in the
  home system.
- **Open:** Number of tiers per planet; time per tier; how long until the first automation (in
  Satisfactory ~1 h); how long until the first other planet (20 h? 100 h?). Is 150 h on planet 1
  too long for a tutorial? Maybe the "tutorial" part is ~10 h and the rest is optional depth.
- **Lock when:** a target curve exists (tier → hours) that the generator can be measured against.

#### D05. World structure
- **Draft** (DESIGN.md §5): galaxy → systems → planets/moons, all from one seed, generated near
  the player. Start on an Earth-like planet in the home system.
- **Open:** Real-scale or compressed planets (Astroneer-small vs huge)? How many planets per
  system? Moons, asteroid belts, gas giants (stations only)? Is the starting planet always
  Earth-like?
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

#### D13. Carry-over
- **Open:** What carries over between planets: knowledge of materials? Blueprints? Machine
  tiers? Proposal (DESIGN.md §4.5): global = knowledge, blueprints, transport tech; local =
  resources, constraints, recipe variants. Risk: too much carry-over → copy-paste the old base;
  too little → frustrating restart.

#### D14. Generator validation and playtime metrics
- **Draft** (DESIGN.md §10): every world completable (reachability, no dead ends); playtime
  estimate per planet; "two seeds feel different" metric.
- **Open:** How to measure "feels different": key materials per role, bottleneck resources,
  planet order, graph shape? How to calibrate the playtime estimate (later: against real play)?

### Phase C: Game systems

#### D15. Player abilities and tools
- **Open:** Movement (jetpack? vehicles?), mining tool, scanner, suit upgrades, inventory size,
  hand crafting vs machines only.

#### D16. Travel between planets and systems
- **Open:** Rockets built in the factory? Launch pads? Ships the player flies? Cutscene travel?
  Cost of travel tied to gravity (D08).

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
  / Unreal. Where the simulation core lives (C#? Rust/C++ via GDExtension?). Laptop performance
  (Iris Plus graphics) as a dev target.

#### D23. Planet rendering, terrain tech, large worlds
- **Open:** Cube-sphere heightmap vs voxel/SDF; LOD; streaming; floating origin / doubles.

#### D24. Save format and determinism rules
- **Open:** Save = seed + diff; versioning (what happens to a world when the generator changes:
  pin the generator version per save?).

### Phase E: Presentation

#### D25. Art direction and generated visuals
- **Open:** Style (stylized/low-poly suits a solo dev and many generated planets); how biomes,
  materials and machines get their look from generated data.

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

## 5. Parking lot

Ideas that don't belong to a decision yet.

- (empty)
