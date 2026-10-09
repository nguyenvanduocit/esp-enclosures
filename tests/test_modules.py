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
    SLIDE_RAILS,
    STOP_AND_HOOK,
    Pcb,
    barb_grips,
    edge_lip,
    grip_problems,
    lid_travel,
    plain_problems,
    pocket_problems,
    pocket_walls,
    shell_and_lid,
    snap_hook,
    standard_notes,
    unit,
)
from printkit.pose import euler_xyz_matrix
from printkit.printability import oriented, overhang_area


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


def test_dragging_a_box_carries_the_fasteners_and_boards_glued_to_it():
    board = ('board', 'Bo', [Box('pcb', (2, 2, 2), (0, 0, 0), '#214f55')])
    drags = {part.id: part.drag for part in small_model(refs=[board]).parts if part.drag}
    assert drags['shell'].carries == ('magnets', 'washers', 'board')
    assert drags['lid'].carries == ('lidMagnets',)
    assert {part.id: part.drag.carries for part in small_model().parts if part.drag}['shell'] == ('magnets', 'washers')


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


def print_overhang(solid, lid):
    """Overhang in mm² of a lone solid turned the way the shell of a module with this lid prints."""
    vertices, triangles = solid.tessellate(0.01, 0.1)
    mesh = trimesh.Trimesh([v.toTuple() for v in vertices], triangles)
    return overhang_area(oriented(mesh, UP[lid]))


SUPERMINI = Pcb((20, 15.35, 16.8), (18, 22.5, 1.6))


@pytest.mark.parametrize('side', ['+x', '-x'])
def test_beam_hook_from_the_bed_wall_grips_the_board_and_prints_without_overhang(side):
    hook = snap_hook(SUPERMINI, side, root=('y', 2.1))
    assert hook.isValid() and len(hook.Solids()) == 1
    assert barb_grips(hook, SUPERMINI) == [(side, approx(0.6), approx(0.2))]
    assert print_overhang(hook, '+y') == approx(0, abs=0.01)


def test_stem_hook_overhangs_only_by_its_catch_ledge():
    pcb = Pcb((20, 20, 8.5), (20.5, 16, 1.6))
    hook = snap_hook(pcb, '+x', root=('z', 2.1))
    assert hook.BoundingBox().zmin == approx(2.1 - 0.5)
    assert print_overhang(hook, '+z') == approx(0.8 * 4, abs=0.01)  # side gap 0.2 + overlap 0.6, 4 mm wide


def test_hanging_hook_holds_the_underside():
    pcb = Pcb((20, 20, 19.8), (32, 24, 1.2), held=-1)
    hook = snap_hook(pcb, '-y', root=('z', 37.9), at=14)
    bb = hook.BoundingBox()
    assert (bb.zmin, bb.zmax) == approx((19.8 - 1.4, 37.9 + 0.5))
    assert barb_grips(hook, pcb) == [('-y', approx(0.6), approx(0.2))]


def test_snap_hook_rejects_a_face_side_and_a_root_across_the_hook():
    with pytest.raises(ValueError):
        snap_hook(SUPERMINI, '+z', root=('z', 2.1))
    with pytest.raises(ValueError):
        snap_hook(SUPERMINI, '+x', root=('x', 2.1))


def test_grip_problems_need_two_sides_and_a_close_barb():
    assert grip_problems([('+x', 0.6, 0.2), ('-x', 0.6, 0.2)]) == []
    assert len(grip_problems([('+x', 0.6, 0.2), ('+x', 0.6, 0.2)])) == 1
    assert len(grip_problems([('+x', 0.6, 0.2), ('-x', 0.3, 0.2)])) == 1
    assert len(grip_problems([('+x', 0.6, 0.2), ('-x', 0.6, 0.5)])) == 1


HOOKED = Pcb((20, 10, 6), (6, 10, 1.6))


def hooked_model(*hooks, pcb=HOOKED):
    spec = ModuleSpec(cells=(2, 1, 1), lid='+z', adds=hooks)
    refs = [('board', 'Bo', [Box('pcb', pcb.size, (20, 10, 6.8), '#214f55')])]
    return small_model(spec=spec, refs=refs, boards=(pcb,))


def test_hooked_board_registers_and_passes_the_hook_check():
    model = hooked_model(*(snap_hook(HOOKED, side, root=('z', 2.1)) for side in ('+y', '-y')))
    assert [name for name, _ in model.checks] == [*CHECK_NAMES, 'Boards held in place']
    for part in model.parts:
        if isinstance(part, PrintPart):
            build_part(part.id, part.build)
    board = run_checks(model)['Boards held in place']['boards'][0]
    assert board['retention'] == 'snap hooks'
    grips = board['grips']
    assert sorted(grip['side'] for grip in grips) == ['+y', '-y']
    assert all(grip['overlap_mm'] == approx(0.6) and grip['gap_mm'] == approx(0.2) for grip in grips)


def test_one_hook_does_not_hold_a_board():
    with pytest.raises(ModelError, match='Boards held in place'):
        run_checks(hooked_model(snap_hook(HOOKED, '+y', root=('z', 2.1))))


def test_a_barb_too_far_from_the_board_fails():
    hooks = [snap_hook(HOOKED, side, root=('z', 2.1), gap=0.5) for side in ('+y', '-y')]
    with pytest.raises(ModelError, match='more than 0.3'):
        run_checks(hooked_model(*hooks))


def test_grip_problems_for_slide_rails_need_opposite_edges_and_a_close_lid():
    rails = [('+x', 0.6, 0.2), ('-x', 0.6, 0.2)]
    assert grip_problems(rails, SLIDE_RAILS, 0.6) == []
    assert any('slide' in p for p in grip_problems(rails, SLIDE_RAILS, 2.4))
    assert any('opposite' in p for p in grip_problems([('+x', 0.6, 0.2), ('+y', 0.6, 0.2)], SLIDE_RAILS, 0.6))


def test_lip_covers_the_edge_and_reaches_over_the_board():
    lip = edge_lip(HOOKED, '-y', wall=2.1, span=(18, 22))
    assert lip.isValid()
    assert barb_grips(lip, HOOKED) == [('-y', approx(0.6), approx(0.2))]
    bb = lip.BoundingBox()
    assert (bb.ymin, bb.ymax) == approx((2.1 - 0.2, 5 + 0.6))  # from 0.2 into the wall to 0.6 over the board
    with pytest.raises(ValueError):
        edge_lip(HOOKED, '-y', wall=6.0, span=(18, 22))


def test_front_stop_and_one_hook_hold_a_board():
    pcb = HOOKED._replace(retention=STOP_AND_HOOK)
    model = hooked_model(snap_hook(pcb, '+y', root=('z', 2.1)), edge_lip(pcb, '-y', wall=2.1, span=(18, 22)), pcb=pcb)
    board = run_checks(model)['Boards held in place']['boards'][0]
    assert board['retention'] == 'front stop and snap hook'
    assert sorted(grip['side'] for grip in board['grips']) == ['+y', '-y']


RAILED = Pcb((10, 9.1, 14.0), (15.4, 11.6, 1.6), retention=SLIDE_RAILS)


def railed_model(pcb):
    rails = tuple(edge_lip(pcb, side, wall=wall, span=(1.9, 15.3)) for side, wall in (('+x', 17.9), ('-x', 2.1)))
    refs = [('board', 'Bo', [Box('pcb', pcb.size, (10, pcb.at[1], 14.8), '#214f55')])]
    return small_model(spec=ModuleSpec(cells=(1, 1, 1), lid='+y', adds=rails), refs=refs, boards=(pcb,))


def test_slide_rails_pass_when_the_closed_lid_stops_the_board():
    board = run_checks(railed_model(RAILED))['Boards held in place']['boards'][0]
    assert board['retention'] == 'slide rails, lid-locked'
    assert board['lid_travel_mm'] == approx(0.6)  # PCB +y edge 14.9, lid skirt from 15.5


def test_slide_rails_fail_when_the_board_can_slide_out_from_under_the_lid():
    short = RAILED._replace(at=(10, 7.9, 14.0), size=(15.4, 9.2, 1.6))  # +y edge at 12.5, 3 mm from the skirt
    assert lid_travel(shell_and_lid(ModuleSpec(cells=(1, 1, 1), lid='+y'))[1], short, unit('+y')) == approx(3.0)
    with pytest.raises(ModelError, match='slide 3.0 mm'):
        run_checks(railed_model(short))
