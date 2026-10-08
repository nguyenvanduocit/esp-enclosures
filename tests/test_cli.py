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
    assert sorted(path.name for path in folder.iterdir()) == [
        "README.md",
        "model.py",
        "thumbnail.png",
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
    assert cli.main(["cad", "alpha"]) == 1
    assert "declares id 'beta'" in capsys.readouterr().err
    assert not (repo / "models/alpha/model.json").exists()
