import json

import numpy as np
import pytest

from printkit import Box, Drag, Model, Solid
from printkit.checks import CheckFailed, clear
from printkit.export import ModelError, export
from printkit.pose import euler_xyz_matrix
from printkit.shapes import block, box_solid, rotated


def demo(check_passes=True, part_id='lid'):
    model = Model('demo', title='Demo', description='d', category='c', status='s', thumbnail='thumbnail.png',
                  dimensions=(20, 20, 12),
                  camera={'position': [60, -60, 60], 'target': [0, 0, 5], 'minDistance': 10, 'maxDistance': 300,
                          'views': [{'id': 'top', 'label': 'Trên', 'offset': [0, -0.01, 100]}]},
                  grid={'size': 100, 'divisions': 20}, print_info={'summary': 'x', 'sections': []})

    @model.part('base', 'Thân', color='#367c85', drag=Drag((0, 0, -1), 20))
    def base():
        return block(20, 20, 10)

    @model.part(part_id, 'Nắp', color='#ded4ba', drag=Drag((0, 0, 1), 20), print_rotation=(0, 180, 0))
    def lid():
        return block(16, 20, 2, x=2, z=10).union(block(4, 4, 1, x=6, z=12))

    model.reference('pin', 'Chốt', [Box('pin', (2, 2, 2), (30, 0, 1), '#c99b49')], drag=Drag((0, 0, 1), 10))
    # The schema requires at least one animation.
    model.animation('lift', 'Nhấc', duration=5, open_pose={part_id: (0, 0, 10)},
                    tracks={part_id: [(0, (0, 0, 0)), (0.5, (0, 0, 10)), (1, (0, 0, 0))]},
                    camera=[(0, (0, 0, 0)), (1, (0, 0, 0))], measure_reveal=(0.3, 0.6))

    @model.check('Lid clears base')
    def lid_clear():
        clear(lid(), base=base())
        if not check_passes:
            raise CheckFailed('forced failure')
        return {'gap_mm': 0.0}

    return model


def test_rotated_matches_pose_convention():
    shape = rotated(block(2, 2, 2, x=10, y=3, z=4), (30, 20, 10))
    center = shape.val().Center()
    expected = euler_xyz_matrix((30, 20, 10)) @ np.array([10, 3, 5])
    assert np.allclose([center.x, center.y, center.z], expected, atol=1e-6)


def test_box_solid_uses_center():
    box = box_solid(Box('pcb', (18, 22.5, 1.6), (1, 2, 12.6), '#214f55')).val().BoundingBox()
    assert np.allclose([box.xmin, box.ymin, box.zmin, box.zmax], [-8, -9.25, 11.8, 13.4], atol=1e-6)


def test_clear_names_obstacle():
    with pytest.raises(CheckFailed, match='base'):
        clear(block(10, 10, 10), base=block(10, 10, 10, z=5))


def test_export_writes_print_frame_meshes_and_poses(tmp_path):
    manifest, report = export(demo(), tmp_path, '../../model.schema.json')
    names = sorted(path.name for path in tmp_path.iterdir())
    assert names == ['assembly.step', 'base.stl', 'lid.stl', 'model.json', 'verification.json']
    lid = next(part for part in manifest['parts'] if part['id'] == 'lid')
    assert lid['rotation'] == [0, 180, 0]
    low, high = report['parts']['lid']['bounds_mm']
    assert low[2] == 0 and np.isclose(low[0], -high[0]) and np.isclose(low[1], -high[1])
    # Viewer pose brings the print-frame bounds back to the installed lid (x 0..10 incl. the tab).
    corners = np.array([low, high])
    world = corners @ euler_xyz_matrix(lid['rotation']).T + np.array(lid['position'])
    assert np.allclose(sorted(world[:, 0]), [-6, 10], atol=1e-6)
    assert np.allclose(sorted(world[:, 2]), [10, 13], atol=1e-6)
    assert report['checks'] == {'Lid clears base': {'gap_mm': 0.0}}
    assert json.loads((tmp_path / 'model.json').read_text()) == manifest


def test_failed_check_writes_nothing(tmp_path):
    export(demo(), tmp_path, '../../model.schema.json')
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    with pytest.raises(ModelError, match='Lid clears base: forced failure'):
        export(demo(check_passes=False), tmp_path, '../../model.schema.json')
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_export_removes_stale_generated_files(tmp_path):
    export(demo(), tmp_path, '../../model.schema.json')
    (tmp_path / 'thumbnail.png').write_bytes(b'keep')
    export(demo(part_id='cover'), tmp_path, '../../model.schema.json')
    names = sorted(path.name for path in tmp_path.iterdir())
    assert names == ['assembly.step', 'base.stl', 'cover.stl', 'model.json', 'thumbnail.png', 'verification.json']


def test_invalid_solid_is_rejected(tmp_path):
    model = demo()

    @model.part('split', 'Rời', color='#000000')
    def split():
        return block(2, 2, 2).union(block(2, 2, 2, x=10))

    with pytest.raises(ModelError, match='split'):
        export(model, tmp_path, '../../model.schema.json')
    assert list(tmp_path.iterdir()) == []


def test_non_check_errors_are_reported_with_check_name(tmp_path):
    model = demo()

    @model.check('Broken lookup')
    def broken():
        raise KeyError('x')

    @model.check('Second failure')
    def second():
        raise CheckFailed('also bad')

    with pytest.raises(ModelError) as error:
        export(model, tmp_path, '../../model.schema.json')
    message = str(error.value)
    assert 'Broken lookup: KeyError' in message
    assert 'Second failure: also bad' in message
    assert list(tmp_path.iterdir()) == []


def test_export_replaces_existing_files(tmp_path):
    export(demo(), tmp_path, '../../model.schema.json')
    (tmp_path / 'base.stl').write_bytes(b'old')
    export(demo(), tmp_path, '../../model.schema.json')
    assert (tmp_path / 'base.stl').read_bytes() != b'old'


def test_overhang_limit_fails_export(tmp_path):
    model = demo()

    @model.part('shelf', 'Kệ', color='#000000', max_overhang_mm2=1)
    def shelf():
        return block(2, 2, 10).union(block(10, 10, 2, z=10))

    with pytest.raises(ModelError, match='shelf: overhang'):
        export(model, tmp_path, '../../model.schema.json')
    assert list(tmp_path.iterdir()) == []


def test_report_includes_printability(tmp_path):
    _, report = export(demo(), tmp_path, '../../model.schema.json')
    assert set(report['printability']) == {'base', 'lid'}
    assert report['printability']['base']['overhang_mm2'] == 0


def test_export_keeps_files_it_did_not_generate(tmp_path):
    (tmp_path / 'stray.stl').write_bytes(b'before any manifest')
    export(demo(), tmp_path, '../../model.schema.json')
    (tmp_path / 'vendor.step').write_bytes(b'user step')
    (tmp_path / 'notes.stl').write_bytes(b'user stl')
    export(demo(part_id='cover'), tmp_path, '../../model.schema.json')
    names = sorted(path.name for path in tmp_path.iterdir())
    assert names == ['assembly.step', 'base.stl', 'cover.stl', 'model.json', 'notes.stl', 'stray.stl',
                     'vendor.step', 'verification.json']


def reference_demo(with_solid):
    model = demo()
    if with_solid:
        model.reference('slab', 'Tấm', [Solid('slab', block(4, 4, 4, x=30), '#c99b49')])
    return model


def test_export_sweeps_only_its_own_reference_files(tmp_path):
    export(reference_demo(True), tmp_path, '../../model.schema.json')
    assert (tmp_path / 'reference' / 'slab.stl').is_file()
    (tmp_path / 'reference' / 'mine.stl').write_bytes(b'user')
    export(reference_demo(False), tmp_path, '../../model.schema.json')
    assert sorted(path.name for path in (tmp_path / 'reference').iterdir()) == ['mine.stl']
    assert not (tmp_path / 'reference' / 'slab.stl').exists()


def test_orientation_warning_is_absolute_print_rotation(tmp_path):
    # The demo lid is declared with print_rotation=(0, 180, 0), which puts its tab on the bed.
    _, report = export(demo(), tmp_path, '../../model.schema.json')
    assert report['printability']['lid']['warning'].startswith('set print_rotation to (0, 0, 180)')
    assert report['warnings'][0].startswith('lid: set print_rotation to (0, 0, 180)')
