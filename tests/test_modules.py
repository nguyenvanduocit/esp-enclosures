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
    Hook,
    Lip,
    Mount,
    Pcb,
    barb_grips,
    beam_length,
    corner_stop,
    mount_report,
    edge_lip,
    edge_stop,
    grip_problems,
    hook_strain,
    travel,
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
    assert hook.solid.isValid() and len(hook.solid.Solids()) == 1
    assert barb_grips(hook.solid, SUPERMINI) == [(side, approx(0.8), approx(0.2))]
    assert print_overhang(hook.solid, '+y') == approx(0, abs=0.01)
    assert hook.length == approx(15.35 - 2 - 2.1)  # from the wall to the start of the barb
    assert beam_length(hook) == approx(hook.length, abs=0.1)


def test_stem_hook_overhangs_only_by_its_catch_ledge_and_has_a_rounded_root():
    pcb = Pcb((20, 20, 9.8), (20.5, 16, 1.6))
    hook = snap_hook(pcb, '+x', root=('z', 2.1), thickness=1.0)
    bb = hook.solid.BoundingBox()
    assert bb.zmin == approx(2.1 - 0.5)
    root = hook.solid.intersect(box((0, 0, 2.1), (40, 40, 2.15))).BoundingBox()
    assert (root.xmin, root.xmax) == approx((30.25 + 0.1 - 0.6, 30.25 + 1.1 + 0.6), abs=0.02)  # 0.6 mm fillet on both faces
    assert bb.xmin == approx(30.25 - 0.8)  # the barb tip
    assert print_overhang(hook.solid, '+z') == approx(0.9 * 4, abs=0.01)  # side gap 0.1 + overlap 0.8, 4 mm wide
    assert hook.length == approx(0.2 + (11.4 - 2.1) - 0.6)  # floor to the catch face, less the fillet
    assert beam_length(hook) == approx(hook.length, abs=0.2)
    assert hook_strain(hook, 0.15) == approx(1.5 * 1.0 * 0.95 / hook.length ** 2)


def test_hanging_hook_holds_the_underside():
    pcb = Pcb((20, 20, 19.8), (32, 24, 1.2), held=-1)
    hook = snap_hook(pcb, '-y', root=('z', 37.9), at=14, fillet=0)
    bb = hook.solid.BoundingBox()
    assert (bb.zmin, bb.zmax) == approx((19.8 - 1.5, 37.9 + 0.5))
    assert barb_grips(hook.solid, pcb) == [('-y', approx(0.8), approx(0.2))]
    assert beam_length(hook) == approx(hook.length, abs=0.1)  # the buried root end is not counted


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


def test_stops_stay_outside_the_board_and_print_cleanly():
    floor_stop = edge_stop(SUPERMINI, '-y', root=('z', 2.1), span=(18, 22))
    wall_stop = edge_stop(SUPERMINI, '-y', root=('y', 2.1), span=(11.2, 13.8))
    corner = corner_stop(SUPERMINI, '+y', wall=37.7)
    pcb = box((11, 4.1, 16.8), (29, 26.6, 18.4))
    for stop in (floor_stop, wall_stop, corner):
        assert stop.isValid()
        assert stop.distance(pcb) == approx(0.2, abs=1e-3)
        assert stop.BoundingBox().zmax == approx(18.4)  # never past the PCB top
    assert print_overhang(wall_stop, '+y') == approx(0, abs=0.01)
    assert print_overhang(corner, '+y') == approx((0.2 + 0.6) * 1.6, abs=0.01)  # only the stop face, gusset at 50°
    assert corner.BoundingBox().xmin == approx(29 - 0.6)


def test_lip_covers_the_edge_and_reaches_over_the_board():
    lip = edge_lip(HOOKED, '-y', wall=2.1, span=(18, 22))
    assert isinstance(lip, Lip) and lip.solid.isValid()
    assert barb_grips(lip.solid, HOOKED) == [('-y', approx(0.8), approx(0.2))]
    bb = lip.solid.BoundingBox()
    assert (bb.ymin, bb.ymax) == approx((2.1 - 0.2, 5 + 0.8))  # from 0.2 into the wall to 0.8 over the board
    with pytest.raises(ValueError):
        edge_lip(HOOKED, '-y', wall=6.0, span=(18, 22))


def test_travel_sweeps_the_board_to_the_first_obstacle_and_names_the_part():
    pieces = [Box('pcb', HOOKED.size, (20, 10, HOOKED.at[2] + 0.8), '#214f55'),
              Box('header', (2, 2, 2), (23.5, 10, HOOKED.at[2] - 1), '#27343c')]
    wall = box((25, 0, 0), (26, 20, 20))
    assert travel([wall], HOOKED, pieces, unit('+x')) == (approx(0.5), 'header')  # the header sticks out 1.5 mm past the PCB
    assert travel([wall], HOOKED, pieces[:1], unit('+x')) == (approx(2.0), 'pcb')
    assert travel([wall], HOOKED, pieces, unit('-x')) == (approx(15.0), None)  # nothing within reach


HOOKED = Pcb((20, 10, 12), (6, 10, 1.6))


def hooks_on(pcb, **options):
    return tuple(snap_hook(pcb, side, root=('z', 2.1), **options) for side in ('+y', '-y'))


def x_stops(pcb, **options):
    return tuple(edge_stop(pcb, side, root=('z', 2.1), span=(8, 12), **options) for side in ('+x', '-x'))


def board_box(pcb):
    return Box('pcb', pcb.size, (pcb.at[0], pcb.at[1], pcb.at[2] + pcb.size[2] / 2), '#214f55')


def held_model(mount, *adds, cells=(2, 1, 1), lid='+z', pieces=None):
    refs = [('board', 'Bo', pieces or [board_box(mount.pcb)])]
    return small_model(spec=ModuleSpec(cells=cells, lid=lid, adds=adds), refs=refs, boards=(mount,))


def hooked_model(*hooks, stops=True, pcb=HOOKED, extra=(), declared=None, pieces=None):
    adds = tuple(part.solid for part in hooks) + (x_stops(pcb) if stops else ()) + tuple(extra)
    return held_model(Mount(pcb, 'board', hooks if declared is None else declared), *adds, pieces=pieces)


def board_report(model):
    return run_checks(model)['Boards held in place']['boards'][0]


def test_hooked_board_registers_and_passes_the_board_check():
    model = hooked_model(*hooks_on(HOOKED))
    assert [name for name, _ in model.checks] == [*CHECK_NAMES, 'Boards held in place']
    for part in model.parts:
        if isinstance(part, PrintPart):
            build_part(part.id, part.build)
    board = board_report(model)
    assert board['retention'] == 'snap hooks'
    assert board['size_range_mm'] == [[5.7, 6.3], [9.7, 10.3]]
    assert sorted(grip['side'] for grip in board['grips']) == ['+y', '-y']
    assert all(grip['overlap_mm'] == approx(0.8) and grip['gap_mm'] == approx(0.2) for grip in board['grips'])
    assert board['travel_mm']['nominal'] == {'+x': 0.2, '-x': 0.2, '+y': 0.1, '-y': 0.1}
    assert board['travel_mm']['undersize'] == {'+x': 0.35, '-x': 0.35, '+y': 0.25, '-y': 0.25}
    assert board['worst_overlap_mm'] == {'nominal': approx(0.7), 'undersize': approx(0.4)}
    assert board['oversize_overlap_mm3'] == 0
    assert board['insertion_lift_mm'] == {'nominal': 0.0, 'oversize': 0.0}  # the lid is on top: the board comes straight down


def test_one_hook_is_no_known_retention():
    with pytest.raises(ModelError, match='do not make snap hooks'):
        run_checks(hooked_model(hooks_on(HOOKED)[0]))


def test_a_barb_too_far_from_the_board_fails():
    with pytest.raises(ModelError, match='more than 0.3'):
        run_checks(hooked_model(*hooks_on(HOOKED, gap=0.5)))


def test_mutation_a_board_without_in_plane_stops_slides_out():
    with pytest.raises(ModelError, match='nominal: the board slides 14.9 mm towards -x'):
        run_checks(hooked_model(*hooks_on(HOOKED), stops=False))


def test_mutation_rigid_lips_cannot_pass_as_hooks():
    lips = tuple(edge_lip(HOOKED, side, wall=wall, span=(18, 22)) for side, wall in (('+y', 17.7), ('-y', 2.1)))
    with pytest.raises(ModelError, match='rigid Lip, not a Hook'):
        run_checks(hooked_model(*lips))


def test_mutation_a_stiff_hook_fails_the_strain_limit():
    low = HOOKED._replace(at=(20, 10, 6))  # stems 5.1 mm long
    with pytest.raises(ModelError, match='bends 6.6% to let a board 0.3 mm larger in'):
        run_checks(hooked_model(*hooks_on(low), pcb=low))


def test_mutation_a_false_beam_length_is_measured_and_rejected():
    hooks = hooks_on(HOOKED)
    liars = tuple(h._replace(length=30.0) for h in hooks)
    with pytest.raises(ModelError, match='declares a 30.00 mm beam but its solid measures 11.'):
        run_checks(hooked_model(*hooks, declared=liars))


def test_mutation_hooks_declared_but_not_built_fail_with_a_message():
    with pytest.raises(ModelError, match='the hook at \\+y is not part of the shell'):
        run_checks(hooked_model(declared=hooks_on(HOOKED)))


def test_mutation_a_hook_moved_away_lets_the_board_slide_off_the_other():
    far = (snap_hook(HOOKED, '+y', root=('z', 2.1), side_gap=0.8), snap_hook(HOOKED, '-y', root=('z', 2.1)))
    with pytest.raises(ModelError, match='nominal: after sliding 0.80 mm towards \\+y'):
        run_checks(hooked_model(*far))


def test_mutation_stops_too_close_for_an_oversize_board():
    tight = tuple(part.solid for part in hooks_on(HOOKED)) + x_stops(HOOKED, side_gap=0.1)
    with pytest.raises(ModelError, match='oversize: a board 0.3 mm larger overlaps the shell'):
        run_checks(held_model(Mount(HOOKED, 'board', hooks_on(HOOKED)), *tight))


def test_mutation_short_barbs_lose_an_undersize_board():
    with pytest.raises(ModelError, match='undersize: after sliding 0.25 mm towards'):
        run_checks(hooked_model(*hooks_on(HOOKED, overlap=0.6)))


def test_mutation_a_part_that_stops_the_board_must_be_declared():
    header = Box('header', (6.2, 2, 0.5), (20, 10, 11.5), '#27343c')  # 0.1 mm past each long edge, under the PCB
    with pytest.raises(ModelError, match='towards \\+x the board is stopped by its header'):
        run_checks(hooked_model(*hooks_on(HOOKED), pieces=[board_box(HOOKED), header]))


def test_mutation_an_undeclared_hook_cannot_grip():
    extra = snap_hook(HOOKED._replace(size=(6, 10, 1.6)), '+x', root=('z', 2.1)).solid
    with pytest.raises(ModelError, match='the grip at \\+x comes from no declared hook or lip'):
        run_checks(hooked_model(*hooks_on(HOOKED), extra=(extra,)))


def test_mutation_a_declared_hook_that_grips_nothing():
    hooks = hooks_on(HOOKED)
    stop = x_stops(HOOKED)[0]
    fake = Hook(stop, '+x', 11.1, 1.2, 0.8)
    with pytest.raises(ModelError, match='the hook or lip at \\+x grips nothing'):
        run_checks(hooked_model(*hooks, declared=hooks + (fake,)))


def test_mutation_something_over_the_board_blocks_insertion():
    arm = box((19, 1.9, 15.0), (21, 10, 15.4))  # a rigid arm from the -y wall 1.4 mm over the PCB
    with pytest.raises(ModelError, match='nominal: the board cannot get in'):
        run_checks(hooked_model(*hooks_on(HOOKED), extra=(arm,)))


def stop_and_hook(**lip_options):
    hook = snap_hook(HOOKED, '+y', root=('z', 2.1))
    lip = edge_lip(HOOKED, '-y', wall=2.1, span=(18, 22), **lip_options)
    return held_model(Mount(HOOKED, 'board', (hook,), (lip,)), hook.solid, lip.solid, *x_stops(HOOKED)), hook


def test_front_stop_and_one_hook_hold_a_board():
    model, hook = stop_and_hook()
    board = board_report(model)
    assert board['retention'] == 'front stop and snap hook'
    assert sorted(grip['side'] for grip in board['grips']) == ['+y', '-y']
    assert board['hook_strain_pct'] == [approx(100 * hook_strain(hook, 0.3), abs=0.01)]  # one hook takes the whole tolerance
    assert board['oversize_overlap_mm3'] == 0  # a larger board sits against the lip and pushes the hook


def test_mutation_a_lip_too_low_to_tilt_under():
    model, _ = stop_and_hook(gap=0.0)
    with pytest.raises(ModelError, match='too low to tilt under'):
        run_checks(model)


RAILED = Pcb((10, 9.1, 14.0), (15.4, 11.6, 1.6), tolerance=0.2)


def railed_model(pcb):
    rails = tuple(edge_lip(pcb, side, wall=wall, span=(1.9, 15.3), side_gap=0.2) for side, wall in (('+x', 17.9), ('-x', 2.1)))
    stop = edge_stop(pcb, '-y', root=('y', 2.1), span=(6, 14))
    return held_model(Mount(pcb, 'board', lips=rails), *(rail.solid for rail in rails), stop, cells=(1, 1, 1), lid='+y')


def test_slide_rails_pass_when_the_closed_lid_stops_the_board():
    board = board_report(railed_model(RAILED))
    assert board['retention'] == 'slide rails, lid-locked'
    assert board['travel_mm']['nominal']['+y'] == approx(0.6)  # PCB +y edge 14.9, lid skirt from 15.5
    assert board['travel_mm']['undersize']['+y'] == approx(0.7)
    assert board['insertion_lift_mm'] == {'nominal': 0.0, 'oversize': 0.0}


def test_mutation_slide_rails_fail_when_the_lid_does_not_stop_the_board():
    short = RAILED._replace(at=(10, 7.9, 14.0), size=(15.4, 9.2, 1.6))  # +y edge at 12.5, 3 mm from the skirt
    with pytest.raises(ModelError, match='nominal: the board slides 3.0 mm towards \\+y'):
        run_checks(railed_model(short))


def test_bme280_end_stops_keep_the_header_off_the_ledge_ends():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).parent.parent / 'models' / 'kit-bme280' / 'model.py'
    spec = importlib.util.spec_from_file_location('kit_bme280_for_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pieces = module.turned(module.bme280(at=module.BOARD))
    mount = Mount(module.PCB, 'board', lips=module.RAILS)
    rails = tuple(rail.solid for rail in module.RAILS)
    for adds, stopped in ((rails + module.LEDGES + module.STOPS, False), (rails + module.LEDGES, True)):
        shell, lid = shell_and_lid(ModuleSpec(module.CELLS, '+y', plain=('-y',), cuts=module.VENTS, adds=adds))
        _, problems = mount_report(mount, shell, lid, pieces, unit('+y'))
        assert any('towards -y the board is stopped by its header' in p for p in problems) == stopped, problems
