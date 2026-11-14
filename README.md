# procedural-game

A 3D factory + exploration game in an endless procedurally generated galaxy, where the progression (resources, recipes, tech tree, goals) is procedural too.

Design phase.

- [DESIGN.md](DESIGN.md): vision and ideas.
- [DESIGN-PLAN.md](DESIGN-PLAN.md): the order of design decisions, the change rule, and the status of each decision.

## Progression generator (milestone 0 prototype)

A headless Python CLI that generates a world's planets, resources, materials, recipes, tiers and needs chain from a seed. No dependencies beyond Python 3.11+.

```bash
python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/gen world --seed 42              # whole world (add --recipes, or --json)
.venv/bin/gen planet --seed 42 --planet 2  # one planet: constraints, variants, why go there
.venv/bin/gen compare 1 2 3                # worlds side by side
.venv/bin/gen graph --seed 42 -o tree.svg  # recipe graph (needs Graphviz; otherwise writes .dot)
.venv/bin/gen check --seeds 1000           # validate many worlds, print stats
```

Design plan tool:

```bash
python tools/plan.py check        # are the process rules followed?
python tools/plan.py next         # what can be decided now
python tools/plan.py impact D03   # what goes stale if D03 changes
python tools/plan.py stale D03    # mark it
```

Tests: `.venv/bin/python -m pytest`.
