import json

import pytest

from printkit import cli, slicer


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "models.json").write_text("[]\n")
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    return tmp_path


def test_new_scaffold_builds(repo):
    assert cli.main(["new", "wall-hook"]) == 0
    folder = repo / "models/wall-hook"
    assert sorted(path.name for path in folder.iterdir() if path.name != "__pycache__") == [
        "README.md",
        "assembly.step",
        "body.stl",
        "model.json",
        "model.py",
        "thumbnail.png",
        "verification.json",
    ]
    assert (folder / "thumbnail.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert json.loads((repo / "models.json").read_text()) == [
        "models/wall-hook/model.json"
    ]
    assert cli.main(["cad", "wall-hook"]) == 0
    manifest = json.loads((folder / "model.json").read_text())
    assert manifest["id"] == "wall-hook" and manifest["parts"][0]["meshes"] == [
        {"src": "body.stl", "color": "#367c85"}
    ]


def test_new_refuses_existing_folder(repo, capsys):
    (repo / "models/taken").mkdir(parents=True)
    assert cli.main(["new", "taken"]) == 1
    assert "already exists" in capsys.readouterr().err


def test_new_rejects_invalid_id(repo, capsys):
    assert cli.main(["new", "9 bad"]) == 1
    assert "invalid model id" in capsys.readouterr().err


def test_cad_rejects_mismatched_id(repo, capsys):
    assert cli.main(["new", "alpha"]) == 0
    model_py = repo / "models/alpha/model.py"
    model_py.write_text(
        model_py.read_text().replace("'alpha', title=", "'beta', title=")
    )
    before = (repo / "models/alpha/model.json").read_bytes()
    assert cli.main(["cad", "alpha"]) == 1
    assert "declares id 'beta'" in capsys.readouterr().err
    assert (repo / "models/alpha/model.json").read_bytes() == before


def test_new_exports_before_listing_the_model(repo):
    assert cli.main(["new", "wall-hook"]) == 0
    listed = json.loads((repo / "models.json").read_text())
    assert listed == ["models/wall-hook/model.json"]
    assert (repo / listed[0]).is_file()


def test_new_failure_removes_folder_and_keeps_catalog(repo, monkeypatch, capsys):
    def fail(model_id):
        raise cli.ModelError("boom")

    monkeypatch.setattr(cli, "cad", fail)
    assert cli.main(["new", "wall-hook"]) == 1
    assert "boom" in capsys.readouterr().err
    assert not (repo / "models/wall-hook").exists()
    assert (repo / "models.json").read_text() == "[]\n"


@pytest.mark.parametrize("bad", ["abc\n", "Abc", "a_b", ""])
def test_new_rejects_ids_with_trailing_newline_or_symbols(repo, capsys, bad):
    assert cli.main(["new", bad]) == 1
    assert "invalid model id" in capsys.readouterr().err
    assert list((repo / "models").glob("*")) == []


def test_cad_unknown_model_names_the_path(repo, capsys):
    assert cli.main(["cad", "typo"]) == 1
    err = capsys.readouterr().err
    assert str(repo / "models/typo/model.py") in err and "Traceback" not in err


def test_cad_names_the_part_that_fails_to_build(repo, capsys):
    assert cli.main(["new", "alpha"]) == 0
    model_py = repo / "models/alpha/model.py"
    model_py.write_text(model_py.read_text().replace("return block(W, L, H)", "raise KeyError('nope')"))
    assert cli.main(["cad", "alpha"]) == 1
    assert "body: KeyError: 'nope'" in capsys.readouterr().err


def fake_slicer(model, out):
    (out / "print").mkdir()
    (out / "print" / f"{model.id}.gcode.3mf").write_bytes(b"PK")
    (out / "print" / "layers.json").write_text("{}")
    return {
        "project": f"print/{model.id}.gcode.3mf",
        "layers": "print/layers.json",
        "slicer": "Bambu Studio test",
        "seconds": 600,
        "grams": 1.5,
        "layerCount": 3,
        "parts": [{"id": "body", "seconds": 600, "grams": 1.5}],
    }


def test_cad_after_slice_says_print_outputs_were_removed(repo, monkeypatch, tmp_path, capsys):
    fake_binary = tmp_path / "BambuStudio"
    fake_binary.write_text("")
    monkeypatch.setattr(slicer, "BINARY", fake_binary)
    monkeypatch.setattr(cli, "slice_model", fake_slicer)
    assert cli.main(["new", "alpha"]) == 0
    assert cli.main(["slice", "alpha"]) == 0
    capsys.readouterr()
    assert (repo / "models/alpha/print").is_dir()
    assert cli.main(["cad", "alpha"]) == 0
    assert "alpha: removed print/ from the earlier slice; run printkit slice alpha to re-slice" in capsys.readouterr().out
    assert not (repo / "models/alpha/print").exists()
    assert cli.main(["cad", "alpha"]) == 0
    assert "removed print/" not in capsys.readouterr().out


def test_slice_without_studio_fails_before_loading_the_model(repo, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(slicer, "BINARY", tmp_path / "missing" / "BambuStudio")
    folder = repo / "models/alpha"
    folder.mkdir(parents=True)
    (folder / "model.py").write_text("raise RuntimeError('model.py was loaded')\n")
    assert cli.main(["slice", "alpha"]) == 1
    err = capsys.readouterr().err
    assert "brew install --cask bambu-studio" in err and "model.py was loaded" not in err
