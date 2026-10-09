"""Kit standard: modules of 20 mm units with flat 2 mm walls and a connector at the centre of every unit on every side.

A connector is a wire port with parts glued flush in pockets drilled from outside: + faces carry 4 round magnets,
- faces one carbon-steel washer. A joint is always magnet to steel and holds at any turn about its axis.
Module coordinates start at the outer corner (CLEAR, CLEAR, CLEAR); `declare` shifts the registered model so the module
is centred in X/Y and sits on Z = 0."""

import itertools
import math
from dataclasses import dataclass
from functools import cache
from typing import NamedTuple

import cadquery as cq
import numpy as np

from printkit.checks import CheckFailed, clear
from printkit.manifest import Box, Drag, Model, Print, Solid, dim, pulse
from printkit.shapes import box_solid

GRID, CLEAR, EDGE_R, WALL = 20.0, 0.1, 1.0, 2.0
LID_PLAIN, LID_SKIRT, SKIRT_WALL, FIT = 1.8, 2.4, 1.2, 0.2
DISC_D, DISC_T, DISC_R = 5.0, 1.5, 5.9
DISC_POCKET = DISC_D + 0.1
WASH_OD, WASH_ID, WASH_T = 12.0, 6.4, 1.6
WASH_POCKET = WASH_OD + 0.1
PORT_D = 5.0
EPS = 0.02

FACES = {
    "+x": (0, 1),
    "-x": (0, -1),
    "+y": (1, 1),
    "-y": (1, -1),
    "+z": (2, 1),
    "-z": (2, -1),
}
# Euler XYZ degrees: UP turns the named face to +Z (shell, opening up), DOWN to -Z (lid, outer face on the bed)
UP = {
    "+z": (0, 0, 0),
    "-z": (180, 0, 0),
    "+x": (0, -90, 0),
    "-x": (0, 90, 0),
    "+y": (90, 0, 0),
    "-y": (-90, 0, 0),
}
DOWN = {
    "+z": (180, 0, 0),
    "-z": (0, 0, 0),
    "+x": (0, 90, 0),
    "-x": (0, -90, 0),
    "+y": (-90, 0, 0),
    "-y": (90, 0, 0),
}


@dataclass(frozen=True)
class ModuleSpec:
    cells: tuple  # units along x, y, z
    lid: str  # the face the lid closes, e.g. '+y'
    plain: tuple = ()  # faces without connectors
    cuts: tuple = ()  # cq.Solids cut out of the shell (USB slot, window, vents), module coordinates
    adds: tuple = ()  # cq.Solids fused to the shell (posts, ribs), module coordinates


def vec(a):
    return cq.Vector(*[float(x) for x in a])


def wp(shape):
    return shape if isinstance(shape, cq.Workplane) else cq.Workplane("XY").add(shape)


def unit(face):
    axis, sign = FACES[face]
    v = np.zeros(3)
    v[axis] = sign
    return v


def kind(face):
    return "magnet" if FACES[face][1] > 0 else "steel"


def axes(face):
    axis = FACES[face][0]
    a, b = np.zeros(3), np.zeros(3)
    a[(axis + 1) % 3] = 1.0
    b[(axis + 2) % 3] = 1.0
    return a, b


def disc_offsets(face):
    a, b = axes(face)
    k = DISC_R / np.sqrt(2)
    return [k * (sa * a + sb * b) for sa in (1, -1) for sb in (1, -1)]


def box(lo, hi):
    return cq.Solid.makeBox(*[hi[i] - lo[i] for i in range(3)], pnt=vec(lo))


def cyl(base, direction, r, length):
    return cq.Solid.makeCylinder(r, length, vec(base), vec(direction))


def ring(base, direction, od, idm, length):
    return cyl(base, direction, od / 2, length).cut(
        cyl(base, direction, idm / 2, length)
    )


def bounds(spec):
    return np.full(3, CLEAR), np.array([c * GRID - CLEAR for c in spec.cells], float)


def outer(cells):
    return tuple(c * GRID - 2 * CLEAR for c in cells)


def connector_faces(spec):
    return [f for f in FACES if f not in spec.plain]


def lid_thickness(spec):
    return WALL if spec.lid in connector_faces(spec) else LID_PLAIN


def face_cells(spec, face):
    lo, hi = bounds(spec)
    axis, sign = FACES[face]
    a1, a2 = (axis + 1) % 3, (axis + 2) % 3
    for i, j in itertools.product(range(spec.cells[a1]), range(spec.cells[a2])):
        c = np.zeros(3)
        c[axis] = hi[axis] if sign > 0 else lo[axis]
        c[a1], c[a2] = (i + 0.5) * GRID, (j + 0.5) * GRID
        yield (i, j), c


def pockets(spec, face):
    """[(centre on the face plane, radius, depth, kind)]: 4 disc pockets per unit on + faces, 1 washer counterbore on - faces."""
    out = []
    for _, c in face_cells(spec, face):
        if kind(face) == "magnet":
            out += [
                (c + o, DISC_POCKET / 2, DISC_T, "magnet") for o in disc_offsets(face)
            ]
        else:
            out.append((c, WASH_POCKET / 2, WASH_T, "steel"))
    return out


def cutters(spec, face):
    n = unit(face)
    out = [cyl(p + n * EPS, -n, r, d + EPS) for p, r, d, _ in pockets(spec, face)]
    thick = lid_thickness(spec) if face == spec.lid else WALL
    out += [
        cyl(c + n * EPS, -n, PORT_D / 2, thick + 2 * EPS)
        for _, c in face_cells(spec, face)
    ]
    return out


def cavity(spec):
    lo, hi = bounds(spec)
    axis, sign = FACES[spec.lid]
    lo_c, hi_c = lo + WALL, hi - WALL
    if sign > 0:
        hi_c[axis] = hi[axis] + 1
    else:
        lo_c[axis] = lo[axis] - 1
    return lo_c, hi_c


def rounded_block(size):
    """A box with every edge rounded by EDGE_R, as the intersection of three prisms rounded along x, y and z.

    `edges().fillet()` blends the corners with sphere patches whose pole is a degenerate edge, and the STL of
    those patches is never watertight. Cylinder-only corners tessellate closed."""
    prisms = [
        cq.Workplane("XY").box(*size, centered=False).edges(f"|{axis}").fillet(EDGE_R)
        for axis in "XYZ"
    ]
    return prisms[0].intersect(prisms[1]).intersect(prisms[2])


def shell_and_lid(spec):
    lo, hi = bounds(spec)
    axis, sign = FACES[spec.lid]
    t = lid_thickness(spec)
    body = rounded_block(hi - lo).val().translate(vec(lo))
    slab_lo, slab_hi = lo - 1, hi + 1
    if sign > 0:
        slab_lo[axis] = hi[axis] - t
    else:
        slab_hi[axis] = lo[axis] + t
    slab = box(slab_lo, slab_hi)
    cav_lo, cav_hi = cavity(spec)
    shell = body.cut(slab).cut(box(cav_lo, cav_hi))
    plate = body.intersect(slab)
    shell_cutters = [
        c
        for face in connector_faces(spec)
        if face != spec.lid
        for c in cutters(spec, face)
    ]
    if spec.adds:
        shell = shell.fuse(*spec.adds)
    tools = [*shell_cutters, *spec.cuts]
    if tools:
        shell = shell.cut(*tools)
    shell = shell.clean()
    if spec.lid in connector_faces(spec):
        plate = plate.cut(*cutters(spec, spec.lid))
    s_lo, s_hi = cav_lo + FIT, cav_hi - FIT  # skirt inset FIT from every wall
    z0 = (hi[axis] - t - LID_SKIRT) if sign > 0 else (lo[axis] + t)
    s_lo[axis], s_hi[axis] = z0, z0 + LID_SKIRT
    h_lo, h_hi = s_lo.copy(), s_hi.copy()
    for a in range(3):
        if a != axis:
            h_lo[a] += SKIRT_WALL
            h_hi[a] -= SKIRT_WALL
    h_lo[axis] -= 1
    h_hi[axis] += 1
    lid = plate.fuse(box(s_lo, s_hi).cut(box(h_lo, h_hi))).clean()
    return shell, lid


class Fastener(NamedTuple):
    solid: object
    kind: str
    centre: np.ndarray
    face: str
    cell: tuple


def fasteners(spec):
    """Every magnet and washer, glued flush in its pocket."""
    out = []
    for face in connector_faces(spec):
        n = unit(face)
        for cell, c in face_cells(spec, face):
            if kind(face) == "magnet":
                for o in disc_offsets(face):
                    out.append(
                        Fastener(
                            cyl(c + o - n * DISC_T, n, DISC_D / 2, DISC_T),
                            "magnet",
                            c + o,
                            face,
                            cell,
                        )
                    )
            else:
                out.append(
                    Fastener(
                        ring(c - n * WASH_T, n, WASH_OD, WASH_ID, WASH_T),
                        "steel",
                        c,
                        face,
                        cell,
                    )
                )
    return out


def fastener_groups(spec):
    """{'magnets', 'washers', 'lidMagnets', 'lidWashers'} -> cq.Compound, empty groups left out."""
    lists = {}
    for f in fasteners(spec):
        name = ("lid" if f.face == spec.lid else "") + (
            "Magnets" if f.kind == "magnet" else "Washers"
        )
        lists.setdefault(name[0].lower() + name[1:], []).append(f.solid)
    return {name: cq.Compound.makeCompound(solids) for name, solids in lists.items()}


def bom(spec):
    items = fasteners(spec)
    return {
        "magnets": sum(f.kind == "magnet" for f in items),
        "washers": sum(f.kind == "steel" for f in items),
    }


def pocket_problems(spec, shell, lid):
    """Failed probes: a pocket not void, no solid floor behind it, a bump in the interior behind it, or a closed port."""
    wrong = 0
    for face in connector_faces(spec):
        n = unit(face)
        on_lid = face == spec.lid
        body = lid if on_lid else shell
        thick = lid_thickness(spec) if on_lid else WALL
        a, _ = axes(face)
        for p, r, depth, _ in pockets(spec, face):
            mid = p + a * (r * 0.5)
            wrong += body.isInside(vec(mid - n * depth / 2), 1e-4)
            wrong += not body.isInside(vec(mid - n * (depth + 0.2)), 1e-4)
            if not on_lid:
                back = vec(mid - n * (WALL + 0.5))
                wrong += shell.isInside(back, 1e-4) and not any(
                    post.isInside(back, 1e-4) for post in spec.adds
                )
        for _, c in face_cells(spec, face):
            wrong += body.isInside(vec(c - n * 0.2), 1e-4) or body.isInside(
                vec(c - n * (thick - 0.2)), 1e-4
            )
    return int(wrong)


def plain_problems(spec, shell):
    """Sample points of plain faces that are not solid wall, ignoring the module's own cut-outs."""
    lo, hi = bounds(spec)
    wrong = 0
    for face in spec.plain:
        if face == spec.lid:
            continue
        n = unit(face)
        axis, sign = FACES[face]
        a1, a2 = (axis + 1) % 3, (axis + 2) % 3
        c0 = (lo + hi) / 2
        c0[axis] = hi[axis] if sign > 0 else lo[axis]
        for g1 in np.arange(lo[a1] + 3, hi[a1] - 2, 5.0):
            for g2 in np.arange(lo[a2] + 3, hi[a2] - 2, 5.0):
                p = c0.copy()
                p[a1], p[a2] = g1, g2
                point = vec(p - n * 0.2)
                if any(cut.isInside(point, 1e-4) for cut in spec.cuts):
                    continue
                wrong += not shell.isInside(point, 1e-4)
    return int(wrong)


def cut_clash_volume(spec):
    cutter_lists = [cutters(spec, face) for face in connector_faces(spec)]
    return sum(
        cut.intersect(c).Volume()
        for cut in spec.cuts
        for face_cutters in cutter_lists
        for c in face_cutters
    )


def pocket_walls(spec):
    """Smallest wall in mm between pockets of adjacent faces, between pockets of one face, and from a magnet pocket to the port.

    Measured on one unit with a connector on every side, because the spec's `cells` do not change these distances."""
    unit_spec = ModuleSpec(cells=(1, 1, 1), lid=spec.lid)
    cyls = []
    for face in FACES:
        n = unit(face)
        cyls += [(face, cyl(p, -n, r, d)) for p, r, d, _ in pockets(unit_spec, face)]
    pairs = list(itertools.combinations(cyls, 2))
    adjacent = min(
        a[1].distance(b[1]) for a, b in pairs if abs(unit(a[0]) @ unit(b[0])) < 0.5
    )
    same_face = min(a[1].distance(b[1]) for a, b in pairs if a[0] == b[0])
    to_port = min(
        cyl(c, -unit(f), PORT_D / 2, WALL).distance(cyl(p, -unit(f), r, d))
        for f in FACES
        for _, c in face_cells(unit_spec, f)
        for p, r, d, k in pockets(unit_spec, f)
        if k == "magnet"
    )
    return adjacent, same_face, to_port


def overlap_fraction(disc_centre, ring_centre):
    """Share of a magnet's face that lies over the washer annulus; both lie in one plane (2D points)."""
    grid = np.linspace(-DISC_D / 2, DISC_D / 2, 81)
    hit = total = 0
    for x, y in itertools.product(grid, grid):
        if x * x + y * y <= (DISC_D / 2) ** 2:
            total += 1
            r = np.hypot(
                disc_centre[0] + x - ring_centre[0], disc_centre[1] + y - ring_centre[1]
            )
            hit += WASH_ID / 2 <= r <= WASH_OD / 2
    return hit / total


MAGNET_COLOR, WASHER_COLOR, LID_COLOR = '#ef5b5b', '#c9d3d9', '#d9d2b8'
GROUP_LABELS = {'magnets': ('Nam châm 5×1.5', MAGNET_COLOR), 'washers': ('Vòng đệm M6', WASHER_COLOR),
                'lidMagnets': ('Nam châm ở nắp', MAGNET_COLOR), 'lidWashers': ('Vòng đệm ở nắp', WASHER_COLOR)}


def standard_notes(spec):
    faces = connector_faces(spec)
    magnets = ', '.join(f.replace('-', '−') for f in faces if kind(f) == 'magnet')
    washers = ', '.join(f.replace('-', '−') for f in faces if kind(f) == 'steel')
    return [
        f'Mặt dương có điểm nối ({magnets}) lắp 4 nam châm tròn 5×1,5 mỗi đơn vị. Mặt âm có điểm nối ({washers}) lắp 1 vòng đệm thép M6 (12×6,4×1,6) mỗi đơn vị. Mối ghép luôn là nam châm hút sắt.',
        'Mua vòng đệm thép mạ kẽm, không mua inox 304/316 vì inox không hút nam châm.',
        'Dán từng nam châm và vòng đệm bằng keo; phía sau chúng chỉ còn sàn 0,4 đến 0,5 mm nên lực hút kéo chúng ra khỏi lỗ nếu không dán.',
        'Không cần lắp kín mọi lỗ: một mối ghép cần 4 nam châm ở mặt dương và 1 vòng đệm ở mặt âm.',
        'Lực hút chưa đo. In một mối ghép và kéo thử trước khi in cả bộ.',
    ]


def moved_piece(piece, offset):
    if isinstance(piece, Box):
        return Box(piece.name, piece.size, tuple(c + o for c, o in zip(piece.center, offset)), piece.color)
    return Solid(piece.name, wp(piece.shape).translate(offset), piece.color)


def reference_solid(piece):
    return box_solid(piece) if isinstance(piece, Box) else wp(piece.shape)


def declare(model, spec, *, color, refs=()):
    """Register shell, lid, fasteners, references, measurements, the open-lid animation and the standard checks."""
    lo, hi = bounds(spec)
    offset = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])
    W, L, H = outer(spec.cells)
    axis = tuple(float(v) for v in unit(spec.lid))

    @cache
    def shapes():
        return shell_and_lid(spec)

    @cache
    def groups():
        return fastener_groups(spec)

    model.part('shell', 'Thân', color=color, drag=Drag(tuple(-v for v in axis), 60),
               print_rotation=UP[spec.lid])(lambda: wp(shapes()[0]).translate(offset))
    model.part('lid', 'Nắp', color=LID_COLOR, drag=Drag(axis, 90),
               print_rotation=DOWN[spec.lid])(lambda: wp(shapes()[1]).translate(offset))
    for name in ('magnets', 'washers', 'lidMagnets', 'lidWashers'):
        if name in groups():
            label, colour = GROUP_LABELS[name]
            model.reference(name, label, [Solid(name, wp(groups()[name]).translate(offset), colour)])
    for ref_id, label, pieces in refs:
        model.reference(ref_id, label, [moved_piece(piece, offset) for piece in pieces])

    lines = [dim((-W / 2, -L / 2, 0), (W / 2, -L / 2, 0), (0, -6, 0), 'Rộng', (0, -4.8, 0)),
             dim((W / 2, -L / 2, 0), (W / 2, L / 2, 0), (6, 0, 0), 'Dài', (7.6, 0, 0)),
             dim((-W / 2, -L / 2, 0), (-W / 2, -L / 2, H), (-6, 0, 0), 'Cao', (-9, 0, 0))]
    model.measure('case', 'Vỏ module', kind='case', follow='shell', lines=lines)

    lift = tuple(50 * v for v in axis)
    moving = ['lid'] + [name for name in ('lidMagnets', 'lidWashers') if name in groups()]
    model.animation('open', 'Mở nắp', duration=8, open_pose={name: lift for name in moving},
                    tracks={name: pulse(lift) for name in moving}, camera=pulse((0, 0, 0)), measure_reveal=(0.34, 0.64))

    @model.check('Outer size equals units x 20 - 0.2 mm')
    def outer_size():
        bb = cq.Compound.makeCompound(list(shapes())).BoundingBox()
        got = (bb.xlen, bb.ylen, bb.zlen)
        if any(abs(g - w) > 0.01 for g, w in zip(got, (W, L, H))):
            raise CheckFailed(f'outer {tuple(round(g, 2) for g in got)} differs from {(W, L, H)}')
        return {'outer_mm': [round(v, 2) for v in got]}

    @model.check('Lid clears shell')
    def lid_clears_shell():
        volume = shapes()[0].intersect(shapes()[1]).Volume()
        if volume >= 1e-3:
            raise CheckFailed(f'lid overlaps shell by {volume:.4f} mm³')

    @model.check('Magnets and washers sit in their pockets')
    def fasteners_in_pockets():
        shell, lid = shapes()
        volume = sum(g.intersect(shell).Volume() + g.intersect(lid).Volume() for g in groups().values())
        bb = cq.Compound.makeCompound(list(groups().values())).BoundingBox()
        out = [bb.xmin < lo[0] - 1e-6, bb.ymin < lo[1] - 1e-6, bb.zmin < lo[2] - 1e-6,
               bb.xmax > hi[0] + 1e-6, bb.ymax > hi[1] + 1e-6, bb.zmax > hi[2] + 1e-6]
        if volume >= 1e-3 or any(out):
            raise CheckFailed(f'fasteners cut the wall by {volume:.4f} mm³ or stand out of the outer box')
        return {'magnets': bom(spec)['magnets'], 'washers': bom(spec)['washers']}

    @model.check('Connectors: pockets void, floors solid, interior flat, ports open')
    def connectors():
        wrong = pocket_problems(spec, *shapes())
        if wrong:
            raise CheckFailed(f'{wrong} probes failed')

    @model.check('Plain faces are solid wall')
    def plain_faces():
        wrong = plain_problems(spec, shapes()[0])
        if wrong:
            raise CheckFailed(f'{wrong} sample points are open')

    @model.check('Cut-outs clear every pocket')
    def cut_outs():
        volume = cut_clash_volume(spec)
        if volume >= 1e-3:
            raise CheckFailed(f'cut-outs overlap pockets by {volume:.4f} mm³')

    @model.check('Reference parts clear shell and lid')
    def reference_parts():
        shell, lid = wp(shapes()[0]), wp(shapes()[1])
        for _, _, pieces in refs:
            for piece in pieces:
                clear(reference_solid(piece), shell=shell, lid=lid)


def kit_model(model_id, *, title, description, spec, color, refs=(), notes=(), sections=()):
    W, L, H = outer(spec.cells)
    size = max(W, L, H)
    grid = int(20 * math.ceil(3 * size / 20))
    # Orbit from the front right above, far enough that the bounding sphere (radius = half the diagonal) fits the 36° view with margin.
    distance = 4 * math.hypot(W, L, H) / 2
    direction = np.array([1.2, -2.0, 1.4]) / np.linalg.norm([1.2, -2.0, 1.4])
    info = {'summary': 'Chưa in thử', 'sections': [
        {'title': 'Lắp nam châm và vòng đệm', 'rows': [], 'notes': [*standard_notes(spec), *notes], 'links': []}, *sections]}
    model = Model(model_id, title=title, description=description, category='Module', status='Chưa in thử',
                  thumbnail='thumbnail.png', dimensions=(W, L, H),
                  camera={'position': [round(float(x), 1) for x in distance * direction + np.array([0, 0, H / 2])], 'target': [0, 0, H / 2],
                          'minDistance': 0.6 * size, 'maxDistance': 6 * size},
                  grid={'size': grid, 'divisions': grid // 10}, print_info=info,
                  print=Print(layer=0.16, first_layer=0.2, walls=3, infill=(15, 'gyroid'), supports=False, brim='auto',
                              extra={'top_shell_layers': 5, 'bottom_shell_layers': 5, 'wall_generator': 'arachne'}))
    declare(model, spec, color=color, refs=refs)
    return model
