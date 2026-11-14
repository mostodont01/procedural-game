import pytest

from progen import generate_world
from progen.analyze import estimate_hours, raw_demand, validate
from progen.generate import PROP_MAX, PROP_MIN
from progen.report import world_json


def test_same_seed_same_world():
    assert world_json(generate_world(7)) == world_json(generate_world(7))


def test_different_seeds_differ_in_substance():
    a, b = generate_world(1), generate_world(2)
    key_a = [n.hazard.tag for n in a.needs]
    key_b = [n.hazard.tag for n in b.needs]
    kinds_a = [p.kind for p in a.planets]
    kinds_b = [p.kind for p in b.planets]
    assert (key_a, kinds_a) != (key_b, kinds_b)


@pytest.mark.parametrize("seed", range(150))
def test_every_world_is_valid(seed):
    v = validate(generate_world(seed))
    assert v.ok, v.errors


def test_every_later_planet_has_a_need_and_later_tier():
    w = generate_world(3)
    tiers = [p.start_tier for p in w.planets]
    assert tiers == sorted(tiers) and len(set(tiers)) == len(tiers)
    assert {n.planet for n in w.needs} == set(range(1, len(w.planets)))
    assert all(p.hazard is not None for p in w.planets[1:])


def test_key_materials_beat_the_normal_range():
    for seed in range(30):
        w = generate_world(seed)
        mats = {m.name: m for m in w.materials}
        for n in w.needs:
            v = mats[n.key_material].props[n.hazard.prop]
            assert v > PROP_MAX if n.hazard.op == ">=" else v < PROP_MIN


def test_normal_materials_stay_in_range():
    w = generate_world(11)
    keys = {n.key_material: n.hazard.prop for n in w.needs}
    for m in w.materials:
        for prop, v in m.props.items():
            if keys.get(m.name) != prop:
                assert PROP_MIN <= v <= PROP_MAX


def test_validation_catches_a_broken_world():
    w = generate_world(5)
    comp = next(r for r in w.recipes if r.kind == "component")
    comp.inputs["Unobtainium"] = 1
    assert not validate(w).ok


def test_validation_catches_a_dead_end():
    w = generate_world(5)
    part = next(r for r in w.recipes if r.kind == "part")
    for r in w.recipes:  # nothing consumes this part any more
        r.inputs.pop(part.name, None)
    assert any("dead end" in e for e in validate(w).errors)


def test_estimate_and_raw_demand():
    w = generate_world(9)
    hours = estimate_hours(w)
    assert len(hours) == len(w.planets) and all(h > 0 for h in hours)
    demand = raw_demand(w, w.tiers[0].milestone)
    assert demand and all(w.items[r].kind == "raw" for r in demand)
