import json

import pytest

from printkit import cli


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
