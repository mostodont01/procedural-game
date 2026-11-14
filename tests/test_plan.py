import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("plan", ROOT / "tools" / "plan.py")
plan = importlib.util.module_from_spec(spec)
sys.modules["plan"] = plan
spec.loader.exec_module(plan)

SAMPLE = """\
| ID | Decision | Depends on | Status |
|---|---|---|---|
| D01 | Pillars | - | locked |
| D02 | Loop | D01 | locked |
| D03 | Pressure | D01, D02 | locked |
| D04 | Scale | D01 | draft |
| D05 | Planets | D03 | open |
"""


def test_real_plan_passes():
    errors, _ = plan.check(plan.parse((ROOT / "DESIGN-PLAN.md").read_text()))
    assert errors == []


def test_dependents_are_transitive_and_exclusive():
    ds = plan.parse(SAMPLE)
    assert plan.dependents(ds, "D02") == ["D03", "D05"]
    assert plan.dependents(ds, "D04") == []


def test_mark_stale_changes_only_dependents():
    text, changed = plan.mark_stale(SAMPLE, "D02")
    assert changed == ["D03"]  # D05 is open, nothing to invalidate
    status = {d.id: d.status for d in plan.parse(text)}
    assert status == {"D01": "locked", "D02": "locked", "D03": "stale", "D04": "draft", "D05": "open"}


def test_locked_on_unlocked_is_an_error():
    bad = SAMPLE.replace("| D05 | Planets | D03 | open |", "| D05 | Planets | D04 | locked |")
    errors, _ = plan.check(plan.parse(bad))
    assert any("D05 is locked but depends on D04" in e for e in errors)


def test_forward_dependency_is_an_error():
    bad = SAMPLE.replace("| D04 | Scale | D01 | draft |", "| D04 | Scale | D05 | draft |")
    errors, _ = plan.check(plan.parse(bad))
    assert any("not earlier" in e for e in errors)


def test_next_prefers_stale():
    text, _ = plan.mark_stale(SAMPLE, "D02")
    assert [d.id for d in plan.ready(plan.parse(text))] == ["D03"]
    assert [d.id for d in plan.ready(plan.parse(SAMPLE))] == ["D04", "D05"]
