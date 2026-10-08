"""Migration check for P1: ported models keep the pre-printkit installed geometry.

Run `uv run python tests/test_p1_regression.py --capture` once on the old layout.
Deleted after both models are ported.
"""

import json
import sys
from pathlib import Path

import numpy as np
import trimesh

from printkit.pose import euler_xyz_matrix

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(__file__).parent / "fixtures/p1-baseline.json"
GEOMETRY_KEYS = {"$schema", "downloads", "parts"}


def world_geometry(manifest_path):
    model = json.loads(manifest_path.read_text())
    folder = manifest_path.parent
    result = {}
    for part in model["parts"]:
        rotation = euler_xyz_matrix(part["rotation"])
        points, volume = [], 0.0
        for mesh in part["meshes"]:
            if "src" in mesh:
                loaded = trimesh.load_mesh(folder / mesh["src"])
                local, volume = loaded.vertices, volume + float(loaded.volume)
            else:
                size, center = np.array(mesh["size"]), np.array(mesh["position"])
                signs = np.array(
                    [[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
                )
                local, volume = center + signs * size / 2, volume + float(np.prod(size))
            points.append(local @ rotation.T + np.array(part["position"]))
        stacked = np.vstack(points)
        result[part["id"]] = {
            "bounds": [stacked.min(0).tolist(), stacked.max(0).tolist()],
            "volume": volume,
        }
    return result


def rounded(value):
    if isinstance(value, float):
        return round(value, 6) + 0.0
    if isinstance(value, list):
        return [rounded(item) for item in value]
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    return value


def comparable(manifest):
    data = {key: value for key, value in manifest.items() if key not in GEOMETRY_KEYS}
    data["parts"] = [
        {key: part.get(key) for key in ("id", "label", "kind", "drag")}
        for part in manifest["parts"]
    ]
    return rounded(data)


def current_manifests():
    return {
        json.loads((ROOT / path).read_text())["id"]: ROOT / path
        for path in json.loads((ROOT / "models.json").read_text())
    }


def capture():
    baseline = {}
    for model_id, path in current_manifests().items():
        baseline[model_id] = {
            "geometry": world_geometry(path),
            "manifest": comparable(json.loads(path.read_text())),
        }
    BASELINE.parent.mkdir(exist_ok=True)
    BASELINE.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n")


def test_installed_geometry_matches_baseline():
    baseline = json.loads(BASELINE.read_text())
    manifests = current_manifests()
    assert set(manifests) == set(baseline)
    for model_id, expected in baseline.items():
        actual = world_geometry(manifests[model_id])
        assert list(actual) == list(expected["geometry"]), model_id
        for part_id, geometry in expected["geometry"].items():
            assert np.allclose(
                actual[part_id]["bounds"], geometry["bounds"], atol=1e-3
            ), (model_id, part_id)
            assert np.isclose(
                actual[part_id]["volume"], geometry["volume"], rtol=1e-4
            ), (model_id, part_id)


def test_non_geometry_fields_match_baseline():
    baseline = json.loads(BASELINE.read_text())
    for model_id, path in current_manifests().items():
        assert (
            comparable(json.loads(path.read_text())) == baseline[model_id]["manifest"]
        ), model_id


if __name__ == "__main__" and "--capture" in sys.argv:
    capture()
