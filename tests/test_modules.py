import itertools

import numpy as np
import pytest
from pytest import approx

from printkit.modules import (
    DISC_R,
    DOWN,
    FACES,
    LID_PLAIN,
    UP,
    WALL,
    ModuleSpec,
    axes,
    bom,
    bounds,
    box,
    cut_clash_volume,
    disc_offsets,
    fastener_groups,
    kind,
    lid_thickness,
    outer,
    overlap_fraction,
    plain_problems,
    pocket_problems,
    pocket_walls,
    shell_and_lid,
    unit,
)
from printkit.pose import euler_xyz_matrix


def test_outer_size_is_units_times_grid_minus_clearance():
    assert outer((2, 4, 2)) == approx((39.8, 79.8, 39.8))


def test_positive_faces_carry_magnets_negative_faces_washers():
    assert [kind(f) for f in ("+x", "+y", "+z")] == ["magnet"] * 3
    assert [kind(f) for f in ("-x", "-y", "-z")] == ["steel"] * 3


@pytest.mark.parametrize("face", list(FACES))
def test_disc_ring_lies_in_the_face_plane_at_radius(face):
    offsets = disc_offsets(face)
    assert len(offsets) == 4
    for offset in offsets:
        assert np.linalg.norm(offset) == approx(DISC_R)
        assert offset @ unit(face) == approx(0)


@pytest.mark.parametrize("face", list(FACES))
def test_print_rotations_put_the_lid_face_up_and_down(face):
    n = unit(face)
    assert euler_xyz_matrix(UP[face]) @ n == approx((0, 0, 1), abs=1e-9)
    assert euler_xyz_matrix(DOWN[face]) @ n == approx((0, 0, -1), abs=1e-9)


def test_a_magnet_lies_over_the_washer_at_every_turn():
    k = DISC_R / np.sqrt(2)
    fractions = []
    for degrees in range(0, 360, 15):
        t = np.radians(degrees)
        c, s = np.cos(t), np.sin(t)
        fractions.append(overlap_fraction((c * k - s * k, s * k + c * k), (0, 0)))
    assert min(fractions) >= 0.4
    assert max(fractions) - min(fractions) < 0.01


SPEC = ModuleSpec(cells=(1, 1, 1), lid="+y")


@pytest.fixture(scope="module")
def built():
    return shell_and_lid(SPEC)


def test_smallest_module_has_exact_outer_size(built):
    import cadquery as cq

    box = cq.Compound.makeCompound(list(built)).BoundingBox()
    assert (box.xlen, box.ylen, box.zlen) == approx((19.8, 19.8, 19.8), abs=0.01)


def test_smallest_module_probes_are_clean(built):
    assert pocket_problems(SPEC, *built) == 0


def test_lid_does_not_touch_shell(built):
    assert built[0].intersect(built[1]).Volume() < 1e-3


def test_pocket_walls_stay_printable():
    adjacent, same_face, to_port = pocket_walls(SPEC)
    assert adjacent >= 0.8 and same_face >= 0.8 and to_port >= 0.8


def test_fastener_counts_of_one_unit():
    assert bom(SPEC) == {"magnets": 12, "washers": 3}
    assert set(fastener_groups(SPEC)) == {"magnets", "washers", "lidMagnets"}


def test_plain_lid():
    spec = ModuleSpec(cells=(1, 1, 1), lid="+y", plain=("+y",))
    assert lid_thickness(spec) == LID_PLAIN
    assert lid_thickness(SPEC) == WALL
    assert not any(name.startswith("lid") for name in fastener_groups(spec))
    assert bom(spec) == {"magnets": 8, "washers": 3}


def test_plain_face_is_solid_and_cut_clash_is_zero():
    spec = ModuleSpec(
        cells=(2, 1, 1), lid="+y", plain=("-y",), cuts=(box((10, 0, 8), (20, 3, 12)),)
    )
    shell, _ = shell_and_lid(spec)
    assert plain_problems(spec, shell) == 0
    assert cut_clash_volume(spec) == approx(0, abs=1e-6)
