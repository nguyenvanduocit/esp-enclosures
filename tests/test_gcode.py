import math

from printkit.gcode import FEATURES, TYPES, arc_points, parse_layers

GCODE = """; HEADER_BLOCK_START
; total layer number: 2
; HEADER_BLOCK_END
M83 ; relative extrusion
G90
; FEATURE: Custom
G1 X0 Y0 F3000
G1 X50 Y0 E5 ; purge line before the first layer is ignored
; CHANGE_LAYER
; Z_HEIGHT: 0.2
; LAYER_HEIGHT: 0.2
G1 E-.8 F1800
G1 X10 Y10 F30000
G1 Z.2
G1 E.8
; FEATURE: Outer wall
G1 X20 Y10 E.5
G1 X20 Y20 E.5
G1 X10 Y10 F30000 ; travel breaks the path
G1 X10 Y20 E.5
; FEATURE: Sparse infill
G1 X15 Y15 E.2
; CHANGE_LAYER
; Z_HEIGHT: 0.36
; LAYER_HEIGHT: 0.16
G1 X30 Y20 F30000
; FEATURE: Mystery feature
G3 X30 Y20 I0 J-5 E1.5 ; full counter-clockwise circle of radius 5
"""


def test_types_cover_every_feature():
    ids = {type_id for type_id, _, _ in TYPES}
    assert set(FEATURES.values()) <= ids and 'other' in ids


def test_arc_points_quarter_circle():
    points = arc_points((10, 0), (0, 10), (0, 0), clockwise=False, step_deg=30)
    assert len(points) == 3 and points[-1] == (0, 10)
    assert all(math.isclose(math.hypot(x, y), 10) for x, y in points)


def test_arc_points_full_circle():
    points = arc_points((5, 0), (5, 0), (0, 0), clockwise=True, step_deg=10)
    assert len(points) == 36 and points[-1] == (5, 0)
    assert points[8][1] < 0  # clockwise from +X goes to -Y first


def test_parse_layers_paths_and_travel():
    data = parse_layers(GCODE)
    assert data['bed'] == [256, 256] and data['unit'] == 0.01
    first, second = data['layers']
    assert (first['z'], first['h']) == (0.2, 0.2) and (second['z'], second['h']) == (0.36, 0.16)
    assert first['paths']['outer_wall'] == [[1000, 1000, 2000, 1000, 2000, 2000], [1000, 1000, 1000, 2000]]
    assert first['paths']['infill'] == [[1000, 2000, 1500, 1500]]
    assert 'other' not in first['paths']  # the purge line came before the first layer
    circle = second['paths']['other'][0]
    assert circle[:2] == [3000, 2000] and circle[-2:] == [3000, 2000] and len(circle) == 2 * 37
