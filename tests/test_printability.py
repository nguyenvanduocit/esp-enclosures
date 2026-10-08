import numpy as np
import trimesh

from printkit.printability import assess, bridges, contact_area, overhang_area, rank_orientations


def box(size, center):
    return trimesh.creation.box(extents=size, transform=trimesh.transformations.translation_matrix(center))


def t_shape():
    """10×10×2 plate on a 2×2×10 stem; concatenated, so the plate underside is fully counted."""
    return trimesh.util.concatenate([box((2, 2, 10), (0, 0, 5)), box((10, 10, 2), (0, 0, 11))])


def test_cube_needs_nothing():
    cube = box((10, 10, 10), (0, 0, 5))
    assert overhang_area(cube) == 0
    assert np.isclose(contact_area(cube), 100)
    assert bridges(cube) == []
    assert assess(cube)['orientations'][0]['rotation'] == [0, 0, 0]
    assert 'warning' not in assess(cube)


def test_t_shape_overhang_and_bridge():
    mesh = t_shape()
    assert np.isclose(overhang_area(mesh), 100)
    assert np.isclose(contact_area(mesh), 4)
    assert bridges(mesh) == [{'z': 10.0, 'size_mm': [10.0, 10.0], 'area_mm2': 100.0}]


def test_flipped_t_warns():
    report = assess(t_shape())
    assert report['orientations'][0]['rotation'] == [180, 0, 0]
    # Flipped, only the stem's top face (buried in the plate of this concatenated mesh) faces down.
    assert report['orientations'][0]['overhang_mm2'] == 4
    assert 'warning' in report and '[180, 0, 0]' in report['warning']


def test_vertical_walls_are_not_overhangs():
    tall = box((2, 20, 30), (0, 0, 15))
    assert overhang_area(tall) == 0
    ranking = rank_orientations(tall)
    assert ranking[0]['contact_mm2'] >= ranking[-1]['contact_mm2']
