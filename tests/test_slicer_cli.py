import stat

import pytest
import trimesh

from printkit import slicer
from printkit.manifest import Print
from printkit.slicer import SliceError, slice_plate

studio = pytest.mark.skipif(
    not slicer.BINARY.exists(), reason="Bambu Studio is not installed"
)


def cube_stl(path, size=20):
    trimesh.creation.box(
        extents=(size, size, size),
        transform=trimesh.transformations.translation_matrix((0, 0, size / 2)),
    ).export(path)
    return path


@studio
def test_slice_plate_applies_settings(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    settings = Print(
        walls=3, infill=(10, "gyroid"), brim=0, extra={"bridge_speed": 25}
    )
    gcode, summary = slice_plate(
        [cube_stl(tmp_path / "cube.stl")], settings, tmp_path / "cube.gcode.3mf", work
    )
    assert summary["seconds"] > 0 and summary["grams"] > 0
    assert summary["layerCount"] == gcode.count("; CHANGE_LAYER")
    assert not (work / "result.json").exists()


@studio
def test_slice_plate_fails_on_unknown_key(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(SliceError, match="not_a_bambu_key"):
        slice_plate(
            [cube_stl(tmp_path / "cube.stl")],
            Print(extra={"not_a_bambu_key": 1}),
            tmp_path / "cube.gcode.3mf",
            work,
        )


def test_run_studio_surfaces_result_json(tmp_path, monkeypatch):
    fake = tmp_path / "BambuStudio"
    fake.write_text(
        '#!/bin/sh\necho \'{"error_string": "process not compatible", "return_code": -17}\' > result.json\nexit 239\n'
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(slicer, "BINARY", fake)
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(SliceError, match="239: process not compatible"):
        slicer.run_studio([tmp_path / "a.stl"], tmp_path, tmp_path / "out.3mf", work)
    assert (work / "result.json").exists()


def test_slice_without_studio_names_install_command(tmp_path, monkeypatch):
    monkeypatch.setattr(slicer, "BINARY", tmp_path / "missing" / "BambuStudio")
    with pytest.raises(SliceError, match="brew install --cask bambu-studio"):
        slicer.slice_model(object(), tmp_path)


def fake_studio(tmp_path, monkeypatch, script):
    fake = tmp_path / "BambuStudio"
    fake.write_text(f"#!/bin/sh\n{script}\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(slicer, "BINARY", fake)
    work = tmp_path / "work"
    work.mkdir()
    return work


def test_run_studio_timeout_is_a_slice_error(tmp_path, monkeypatch):
    work = fake_studio(tmp_path, monkeypatch, "exec sleep 5")
    monkeypatch.setattr(slicer, "TIMEOUT_S", 1)
    with pytest.raises(SliceError, match="did not finish"):
        slicer.run_studio([tmp_path / "a.stl"], tmp_path, tmp_path / "out.3mf", work)


def test_run_studio_without_project_is_a_slice_error(tmp_path, monkeypatch):
    work = fake_studio(tmp_path, monkeypatch, "exit 0")
    with pytest.raises(SliceError, match="no readable project"):
        slicer.run_studio([tmp_path / "a.stl"], tmp_path, tmp_path / "out.3mf", work)


def test_run_studio_survives_malformed_result_json(tmp_path, monkeypatch):
    work = fake_studio(
        tmp_path, monkeypatch, "echo '{not json' > result.json\necho boom >&2\nexit 3"
    )
    with pytest.raises(SliceError, match="exited 3: boom"):
        slicer.run_studio([tmp_path / "a.stl"], tmp_path, tmp_path / "out.3mf", work)
