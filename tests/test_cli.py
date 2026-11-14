import json

from progen.cli import main


def test_world(capsys):
    assert main(["world", "--seed", "4", "--recipes"]) == 0
    out = capsys.readouterr().out
    assert "NEEDS CHAIN" in out and "VALIDATION: OK" in out and "RECIPES" in out


def test_world_json(capsys):
    assert main(["world", "--seed", "4", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["seed"] == 4 and data["planets"][0]["kind"] == "earthlike"


def test_planet(capsys):
    assert main(["planet", "--seed", "4", "--planet", "1"]) == 0
    assert "TO GET HERE" in capsys.readouterr().out


def test_planet_out_of_range():
    assert main(["planet", "--seed", "4", "--planet", "99"]) == 2


def test_graph_dot(tmp_path, capsys):
    out = tmp_path / "g.dot"
    assert main(["graph", "--seed", "4", "-o", str(out)]) == 0
    assert out.read_text().startswith("digraph")


def test_compare(capsys):
    assert main(["compare", "1", "2"]) == 0
    assert "needs" in capsys.readouterr().out


def test_check(capsys):
    assert main(["check", "--seeds", "10"]) == 0
    assert "10 worlds, 10 valid" in capsys.readouterr().out
