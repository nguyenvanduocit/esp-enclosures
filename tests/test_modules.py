import cadquery as cq
import numpy as np
import pytest
import trimesh
from pytest import approx

from printkit.cli import placeholder_png
from printkit.export import ModelError, built as build_part, export, run_checks
from printkit.manifest import Box, PrintPart
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
    box,
    cut_clash_volume,
    cyl,
    disc_offsets,
    fastener_groups,
    kind,
    kit_model,
    lid_thickness,
    outer,
    overlap_fraction,
    plain_problems,
    pocket_problems,
    pocket_walls,
    shell_and_lid,
    standard_notes,
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
    size = cq.Compound.makeCompound(list(built)).BoundingBox()
    assert (size.xlen, size.ylen, size.zlen) == approx((19.8, 19.8, 19.8), abs=0.01)


def test_smallest_module_probes_are_clean(built):
    assert pocket_problems(SPEC, *built) == 0


def test_lid_does_not_touch_shell(built):
    assert built[0].intersect(built[1]).Volume() < 1e-3


def test_pocket_walls_stay_printable():
    adjacent, same_face, to_port = pocket_walls(SPEC)
    assert adjacent >= 0.8 and same_face >= 0.8 and to_port >= 0.8
    assert (adjacent, same_face, to_port) == approx((2.37, 3.24, 0.85), abs=0.02)


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


LID_ONLY = ModuleSpec(
    cells=(1, 1, 1), lid="+y", plain=tuple(f for f in FACES if f != "+y")
)
ADDS_AND_CUTS = ModuleSpec(
    cells=(1, 1, 1),
    lid="+y",
    plain=("-y",),
    adds=(cyl((4, 4, 1.6), (0, 0, 1), 1.5, 6),),
    cuts=(box((8, 0, 8), (12, 3, 12)),),
)
ZLID = ModuleSpec(cells=(2, 1, 1), lid="-z")
PRINT_SPECS = {
    "unit": SPEC,
    "long-z-lid": ZLID,
    "plain-lid": ModuleSpec(cells=(1, 1, 1), lid="+y", plain=("+y",)),
    "adds-and-cuts": ADDS_AND_CUTS,
    "lid-only-connector": LID_ONLY,
}


@pytest.mark.parametrize("spec", PRINT_SPECS.values(), ids=PRINT_SPECS.keys())
def test_shell_and_lid_are_each_one_valid_solid(spec):
    for part in shell_and_lid(spec):
        assert part.isValid()
        assert len(part.Solids()) == 1


@pytest.mark.parametrize("spec", [ZLID, ADDS_AND_CUTS], ids=["long-z-lid", "adds-and-cuts"])
def test_pocket_probes_are_clean_on_other_lids_and_posts(spec):
    assert pocket_problems(spec, *shell_and_lid(spec)) == 0


CHECK_NAMES = ['Outer size equals units x 20 - 0.2 mm', 'Lid clears shell', 'Magnets and washers sit in their pockets',
               'Connectors: pockets void, floors solid, interior flat, ports open', 'Plain faces are solid wall',
               'Cut-outs clear every pocket', 'Reference parts clear shell and lid']


def small_model(**changes):
    options = dict(title='T', description='d', spec=SPEC, color='#367c85')
    options.update(changes)
    return kit_model('kit-test', **options)


def test_kit_model_registers_parts_references_and_checks():
    model = small_model()
    ids = [part.id for part in model.parts]
    assert ids == ['shell', 'lid', 'magnets', 'washers', 'lidMagnets']
    assert [name for name, _ in model.checks] == CHECK_NAMES
    assert [a['id'] for a in model.animations] == ['open']
    assert model.info['dimensions'] == approx([19.8, 19.8, 19.8])


def test_kit_model_builds_single_solids_and_passes_its_checks():
    model = small_model()
    for part in model.parts:
        if isinstance(part, PrintPart):
            build_part(part.id, part.build)
    results = run_checks(model)
    assert results['Outer size equals units x 20 - 0.2 mm']['outer_mm'] == approx([19.8, 19.8, 19.8])


def test_standard_note_names_the_connector_faces_of_each_module():
    note = standard_notes(ModuleSpec(cells=(1, 1, 1), lid='+y', plain=('+z', '-y')))[0]
    assert 'Mặt dương có điểm nối (+x, +y)' in note
    assert 'Mặt âm có điểm nối (−x, −z)' in note
    assert '+z' not in note and '−y' not in note
    assert 'Mặt dương có điểm nối (+x, +y, +z)' in standard_notes(ModuleSpec(cells=(1, 1, 1), lid='+y'))[0]


@pytest.mark.parametrize("cells", [(1, 1, 1), (2, 2, 2), (2, 4, 2), (4, 1, 2)])
def test_camera_frames_the_whole_module(cells):
    camera = small_model(spec=ModuleSpec(cells=cells, lid='+y')).info['camera']
    radius = np.linalg.norm(outer(cells)) / 2
    distance = np.linalg.norm(np.array(camera['position']) - np.array(camera['target']))
    assert distance * np.sin(np.radians(18)) >= 1.15 * radius  # vertical fov 36 degrees, 15 % margin
    assert camera['minDistance'] < distance < camera['maxDistance']


def test_reference_inside_wall_fails():
    bad = [('big', 'Big', [Box('b', (30, 30, 30), (10, 10, 10), '#fff')])]
    with pytest.raises(ModelError, match='Reference parts clear shell and lid'):
        run_checks(small_model(refs=bad))


def test_cut_into_pocket_fails():
    spec = ModuleSpec(cells=(1, 1, 1), lid='+y', cuts=(box((8, 0, 8), (12, 3, 12)),))
    with pytest.raises(ModelError, match='Cut-outs clear every pocket'):
        run_checks(small_model(spec=spec))


def test_plain_lid_registers_no_lid_fasteners_and_moves_only_the_lid():
    model = small_model(spec=ModuleSpec(cells=(1, 1, 1), lid='+y', plain=('+y',)))
    ids = [part.id for part in model.parts]
    assert 'lidMagnets' not in ids and 'lidWashers' not in ids
    assert ids == ['shell', 'lid', 'magnets', 'washers']
    assert list(model.animations[0]['openPose']) == ['lid']
    assert [track['part'] for track in model.animations[0]['tracks']] == ['lid']


@pytest.mark.parametrize('spec', [
    ModuleSpec(cells=(1, 1, 1), lid='+y'),
    ModuleSpec(cells=(1, 1, 1), lid='-z', plain=('+x',), cuts=(box((17, 6, 6), (21, 14, 14)),)),
], ids=['lid +y', 'lid -z with a plain face and a cut-out'])
def test_exported_meshes_are_watertight_single_bodies(tmp_path, spec):
    folder = tmp_path / 'models' / 'kit-test'
    folder.mkdir(parents=True)
    (folder / 'thumbnail.png').write_bytes(placeholder_png())
    export(small_model(spec=spec), folder, '../../model.schema.json')
    for name in ('shell', 'lid'):
        mesh = trimesh.load_mesh(folder / f'{name}.stl')
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split()) == 1, name
