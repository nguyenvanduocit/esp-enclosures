import math

import manifold3d as m3
import numpy as np
import pytest

from printkit import art
from printkit.shapes import block


def test_sdf_primitives_are_negative_inside():
    assert art.ellipsoid((0, 0, 0), (0, 0, 0), (3, 2, 1)) < 0 < art.ellipsoid((4, 0, 0), (0, 0, 0), (3, 2, 1))
    assert math.isclose(art.capsule((0, 3, 0), (-5, 0, 0), (5, 0, 0), 1), 2)
    assert math.isclose(art.round_box((0, 0, 4), (2, 2, 2), 0.5), 2)
    assert art.triangle_2d(0, 0.2, (-1, 0), (1, 0), (0, 1)) < 0 < art.triangle_2d(0, 2, (-1, 0), (1, 0), (0, 1))


def test_smooth_min_and_max_blend_within_k():
    assert art.smin(1.0, 1.0, 2.0) == pytest.approx(0.5)
    assert art.smin(0.0, 5.0, 2.0) == 0.0  # farther apart than k: plain min
    assert art.smax(1.0, 1.0, 2.0) == pytest.approx(1.5)


def test_level_set_meshes_a_sphere():
    sphere = art.level_set(lambda p: art.length(*p) - 5, (-6, -6, -6, 6, 6, 6), 0.5)
    assert sphere.status() == m3.Error.NoError
    assert sphere.volume() == pytest.approx(4 / 3 * math.pi * 125, rel=0.03)


def test_weathering_is_seeded_and_bounded():
    points = np.random.default_rng(0).random((500, 3)) * 50
    a, b = art.weathering(points, 1), art.weathering(points, 1)
    assert np.array_equal(a, b) and a.min() >= 0 and a.max() <= 1
    assert not np.array_equal(a, art.weathering(points, 2))


def test_mask_weight_protects_bed_and_boxes():
    points = np.array([[0, 0, 0.5], [0, 0, 10], [20, 0, 10]])
    weight = art.mask_weight(points, [((15, -5, 5), (25, 5, 15))])
    assert weight.tolist() == [0, 1, 0]


def test_erode_moves_material_inward_only():
    blank = art.box((0, 0, 0), (20, 20, 20))
    eroded = art.erode(blank, seed=3, amplitude=1.0)
    assert (eroded - blank).volume() < 1e-3
    assert eroded.volume() < blank.volume() - 1


def test_erode_leaves_masked_regions_untouched():
    blank = art.box((0, 0, 0), (20, 20, 20))
    eroded = art.erode(blank, seed=3, amplitude=1.0, mask=[((-5, -5, -5), (25, 25, 25))])
    assert eroded.volume() == pytest.approx(blank.volume(), abs=1e-3)


def test_erode_rejects_large_amplitude():
    with pytest.raises(ValueError, match='amplitude'):
        art.erode(art.box((0, 0, 0), (5, 5, 5)), seed=1, amplitude=2.0)


def test_to_manifold_keeps_cadquery_volume():
    shape = block(10, 20, 5).faces('>Z').workplane().hole(4)
    assert art.to_manifold(shape).volume() == pytest.approx(shape.val().Volume(), rel=1e-3)


def test_canonical_mesh_ignores_input_order():
    plate = art.box((0, 0, 0), (30, 30, 3))
    for x in (5, 15, 25):
        plate -= m3.Manifold.cylinder(10, 2, 2, 16).translate((x, 15, -1))
    mesh = plate.to_mesh()
    tris = np.asarray(mesh.tri_verts)[::-1][:, [1, 2, 0]]  # same surface, other order
    shuffled = art.manifold(np.asarray(mesh.vert_properties)[:, :3], tris)
    first, second = art.canonical_mesh(plate), art.canonical_mesh(shuffled)
    assert np.array_equal(first[0], second[0]) and np.array_equal(first[1], second[1])
    assert first[2] == 0
