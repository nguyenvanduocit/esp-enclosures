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


SNAP_HOOKS, SLIDE_RAILS, STOP_AND_HOOK = 'snap hooks', 'slide rails, lid-locked', 'front stop and snap hook'


class Pcb(NamedTuple):
    """A board the shell holds. `at` is the centre of the PCB underside (as in printkit.library.electronics), `size` is
    (x, y, thickness); `held` is +1 when barbs or rails hold the top face down, -1 when they hold the underside up;
    `tolerance` is how far the board's x and y sizes may differ from `size` between sellers (±)."""
    at: tuple
    size: tuple
    held: int = 1
    tolerance: float = 0.3


class Hook(NamedTuple):
    """A printed snap hook: its solid, the PCB side it holds, its bending length and thickness, and how far its barb
    reaches over a board of nominal size."""
    solid: object
    side: str
    length: float
    thickness: float
    overlap: float


class Lip(NamedTuple):
    """A rigid lip over one PCB edge."""
    solid: object
    side: str


class Mount(NamedTuple):
    """How a module holds one board: the board, the reference id of its parts, its snap hooks and its rigid lips.
    Two or more hooks make SNAP_HOOKS, one hook and lips STOP_AND_HOOK, lips on two opposite edges SLIDE_RAILS."""
    pcb: Pcb
    ref: str
    hooks: tuple = ()
    lips: tuple = ()


HOOK_T, HOOK_W, HOOK_SIDE_GAP, HOOK_GAP, HOOK_OVERLAP, HOOK_LAND = 1.2, 4.0, 0.2, 0.2, 0.6, 0.4
HOOK_FILLET = 0.6  # a stem's root is rounded on both faces so the bend does not start at a sharp corner
HOOK_EMBED = 0.5  # a hook root reaches this far into its wall so the fuse is solid
HOOK_SLOPE = 1.2  # support chamfers rise 50°, so slicers never count them as 45° overhang
LIP_EMBED = 0.2  # lips and stops are fused along their whole length, so they reach only this far into the wall and stay off pocket floors
MIN_OVERLAP, MAX_GAP, MAX_TRAVEL, MAX_STRAIN = 0.4, 0.3, 1.0, 0.02
IN_PLANE = ('+x', '-x', '+y', '-y')


def held_face(pcb):
    return pcb.at[2] + (pcb.size[2] if pcb.held > 0 else 0)


def _frame(pcb, side):
    """Local axes at the `side` edge of `pcb`: u out of the board, v along the edge, w out of the held face. The origin
    lies on the edge line in the held face plane, at module coordinate 0 along v."""
    axis, sign = FACES[side]
    if axis == 2:
        raise ValueError(f'{side} is not a PCB edge side')
    e = 1 - axis
    basis = {'u': unit(side), 'v': np.eye(3)[e], 'w': np.array([0.0, 0.0, float(pcb.held)])}
    origin = np.zeros(3)
    origin[axis] = pcb.at[axis] + sign * pcb.size[axis] / 2
    origin[2] = held_face(pcb)
    return axis, sign, e, basis, origin


def _prism(origin, basis, axes, outline, span):
    """Prism with `outline` in local axes axes[0], axes[1] (keys of `basis`), extruded along axes[2] over `span`."""
    a, b, c = (basis[k] for k in axes)
    plane = cq.Plane(origin=vec(origin + span[0] * c), xDir=vec(a), normal=vec(c))
    flip = 1.0 if np.dot(plane.yDir.toTuple(), b) > 0 else -1.0
    points = [(float(p), float(flip * q)) for p, q in outline]
    return cq.Workplane(plane).polyline(points).close().extrude(float(span[1] - span[0])).val()


def _arc(centre, r, start, end, steps=6):
    return [(centre[0] + r * math.cos(math.radians(t)), centre[1] + r * math.sin(math.radians(t)))
            for t in np.linspace(start, end, steps + 1)]


def snap_hook(pcb, side, *, root, at=None, width=HOOK_W, thickness=HOOK_T, side_gap=HOOK_SIDE_GAP, gap=HOOK_GAP,
              overlap=HOOK_OVERLAP, land=HOOK_LAND, back=0.0, fillet=HOOK_FILLET):
    """A printed snap hook at `side` ('+x', '-x', '+y', '-y') of `pcb`, as a Hook in module coordinates.

    The hook stands `side_gap` outside the PCB edge. Its barb reaches `overlap` over the held face, `gap` beyond it, and
    a 45° lead-in on the barb lets the board push the hook aside. `root` = (axis, coordinate) of the inner wall face the
    hook grows from. Axis 'z' makes a stem from the floor or ceiling, its root rounded by `fillet` on both faces. The
    axis along the edge makes a beam from that wall, as tall as the PCB edge plus `gap` and `back`, with the barb on its
    last `width` mm; that end is chamfered towards the wall so the beam prints without support when the wall lies on the
    bed. `at` is the barb centre along the edge, by default the middle of the edge. The Hook's length is the bending
    length from the root (past its fillet) to the barb, for the strain check."""
    axis, sign, e, basis, origin = _frame(pcb, side)
    centre = pcb.at[e] if at is None else at
    inner, outside = side_gap, side_gap + thickness
    top = gap + land + side_gap + overlap
    barb = [(-overlap, gap), (-overlap, gap + land), (inner, top), (outside, top)]
    root_axis, root_at = root
    if root_axis == 'z':
        surface = (root_at - origin[2]) * pcb.held
        foot = surface - HOOK_EMBED
        r = fillet
        rounded_out = _arc((outside + r, surface + r), r, 270, 180) if r > 0 else [(outside, surface)]
        rounded_in = _arc((inner - r, surface + r), r, 0, -90) if r > 0 else [(inner, surface)]
        outline = [(outside + r, foot), *rounded_out, *barb[::-1], (inner, gap), *rounded_in, (inner - r, foot)]
        solid = _prism(origin, basis, 'uwv', outline, (centre - width / 2, centre + width / 2))
        return Hook(solid, side, gap + land - surface - r, thickness, overlap)
    if root_axis != 'xyz'[e]:
        raise ValueError(f"a hook at {side} grows from the floor or ceiling (z) or from a wall across {'xyz'[e]}")
    s = 1.0 if centre > root_at else -1.0
    start, v0, tip = root_at - s * HOOK_EMBED, centre - s * width / 2, centre + s * width / 2
    low = -pcb.size[2] - back
    body = _prism(origin, basis, 'uwv', [(inner, low), (outside, low), (outside, gap), (inner, gap)], sorted((start, tip)))
    end = _prism(origin, basis, 'uwv', [(outside, gap), *barb], sorted((v0, tip)))
    rise = [(v0 - s * HOOK_SLOPE, gap - 1), (v0 + s * HOOK_SLOPE * (top - gap + 1), top + 1),
            (v0 - s * 10, top + 1), (v0 - s * 10, gap - 1)]
    lean = [(outside + 1, v0 - s * HOOK_SLOPE * (thickness + 1)), (-overlap - 1, v0 + s * HOOK_SLOPE * (inner + overlap + 1)),
            (-overlap - 1, v0 - s * 10), (outside + 1, v0 - s * 10)]
    end = end.cut(_prism(origin, basis, 'vwu', rise, (-overlap - 1, outside + 1)))
    end = end.cut(_prism(origin, basis, 'uvw', lean, (gap - 1, top + 1)))
    return Hook(body.fuse(end).clean(), side, abs(v0 - root_at), thickness, overlap)


def edge_lip(pcb, side, *, wall, span, side_gap=HOOK_SIDE_GAP, gap=HOOK_GAP, overlap=HOOK_OVERLAP, thickness=HOOK_T,
             embed=LIP_EMBED):
    """A rigid lip fused to the wall behind the `side` edge of `pcb`, over `span` (lo, hi) along that edge, as a Lip.

    It reaches `overlap` over the held face, `gap` beyond it, and `thickness` thick; from the wall to `side_gap` off the
    PCB edge it also covers the edge itself, so the board cannot slide towards the wall. `wall` is the coordinate of the
    inner wall face across the side axis. Two lips on opposite edges make slide rails; with a snap hook opposite, a front stop."""
    axis, sign, e, basis, origin = _frame(pcb, side)
    back = (wall - origin[axis]) * sign + embed
    if back <= side_gap:
        raise ValueError(f'the wall at {wall} is not behind the {side} edge')
    top = gap + thickness
    outline = [(back, -pcb.size[2]), (back, top), (-overlap, top), (-overlap, gap), (side_gap, gap), (side_gap, -pcb.size[2])]
    return Lip(_prism(origin, basis, 'uwv', outline, sorted(span)), side)


def edge_stop(pcb, side, *, root, span, side_gap=HOOK_SIDE_GAP, thickness=HOOK_T, embed=LIP_EMBED):
    """A rigid block `side_gap` outside the `side` edge of `pcb`, over `span` along that edge, that stops the board
    sliding that way; it ends in the held face plane, so it never reaches past the PCB towards the barbs.

    `root` = ('z', floor or ceiling) stands it, `thickness` thick, on that wall; root = (side axis, wall) builds it out
    from the wall behind the edge, as deep as the PCB edge plus `thickness`."""
    axis, sign, e, basis, origin = _frame(pcb, side)
    root_axis, root_at = root
    if root_axis == 'z':
        foot = (root_at - origin[2]) * pcb.held - embed
        outline = [(side_gap, foot), (side_gap + thickness, foot), (side_gap + thickness, 0.0), (side_gap, 0.0)]
    elif root_axis == 'xyz'[axis]:
        back = (root_at - origin[axis]) * sign + embed
        if back <= side_gap:
            raise ValueError(f'the wall at {root_at} is not behind the {side} edge')
        low = -pcb.size[2] - thickness
        outline = [(side_gap, low), (back, low), (back, 0.0), (side_gap, 0.0)]
    else:
        raise ValueError(f"a stop at {side} stands on the floor or ceiling (z) or on the wall across {'xyz'[axis]}")
    return _prism(origin, basis, 'uwv', outline, sorted(span))


def corner_stop(pcb, side, *, wall, reach=HOOK_OVERLAP, side_gap=HOOK_SIDE_GAP, thickness=HOOK_T, embed=LIP_EMBED):
    """A rigid stop `side_gap` outside the `side` edge of `pcb`, reaching `reach` along that edge past the PCB corner
    next to `wall` (the inner face of the side wall across the edge), as tall as the PCB edge. A gusset holds it out
    from that wall; the gusset's face towards the board rises at 50°, so with the side direction up in print only the
    stop face itself, (side_gap + reach) x PCB thickness, overhangs."""
    axis, sign, e, basis, origin = _frame(pcb, side)
    d = -1.0 if wall > pcb.at[e] else 1.0  # along the edge, from the wall towards the board
    corner = pcb.at[e] - d * pcb.size[e] / 2
    tip, gusset, end = corner + d * reach, corner - d * side_gap, wall - d * embed
    if (end - gusset) * d >= 0:
        raise ValueError(f'the wall at {wall} is not beyond the PCB corner at {corner}')
    low = side_gap - HOOK_SLOPE * abs(end - gusset)
    outline = [(side_gap, tip), (side_gap + thickness, tip), (side_gap + thickness, end), (low, end), (side_gap, gusset)]
    return _prism(origin, basis, 'uvw', outline, (-pcb.size[2], 0.0))


def barb_grips(shell, pcb, depth=2.0):
    """[(side, overlap, gap)] for each piece of `shell` inside the PCB outline within `depth` of the held face.

    overlap is how far the piece reaches over the face from the edge it hugs (of the edges it touches, the one it reaches
    least far from, so a rail along a whole edge counts once), gap its distance from the face."""
    face = held_face(pcb)
    lo = np.array([pcb.at[0] - pcb.size[0] / 2, pcb.at[1] - pcb.size[1] / 2])
    hi = lo + np.array(pcb.size[:2])
    z0, z1 = sorted((face, face + pcb.held * depth))
    grips = []
    for piece in shell.intersect(box((lo[0], lo[1], z0), (hi[0], hi[1], z1))).Solids():
        if piece.Volume() < 1e-6:
            continue
        bb = piece.BoundingBox()
        low, high = np.array([bb.xmin, bb.ymin]), np.array([bb.xmax, bb.ymax])
        gap = bb.zmin - face if pcb.held > 0 else face - bb.zmax
        touched = []
        for side in IN_PLANE:
            axis, sign = FACES[side]
            if sign > 0 and high[axis] > hi[axis] - 1e-3:
                touched.append((float(hi[axis] - low[axis]), side))
            elif sign < 0 and low[axis] < lo[axis] + 1e-3:
                touched.append((float(high[axis] - lo[axis]), side))
        if touched:
            overlap, side = min(touched)
            grips.append((side, overlap, float(gap)))
    return grips


def grip_problems(grips):
    """Why `grips` do not hold a board: fewer than two sides gripped by MIN_OVERLAP, or a barb further than MAX_GAP."""
    sides = {side for side, overlap, _ in grips if overlap >= MIN_OVERLAP - 1e-3}
    problems = [] if len(sides) >= 2 else [f'barbs reach {MIN_OVERLAP} mm over the board on {len(sides)} side(s), need 2']
    return problems + [f'barb at {side} is {gap:.2f} mm from the board, more than {MAX_GAP}' for side, _, gap in grips if gap > MAX_GAP]


def retention(mount):
    sides = {lip.side for lip in mount.lips}
    if len(mount.hooks) >= 2 and not mount.lips:
        return SNAP_HOOKS
    if len(mount.hooks) == 1 and mount.lips:
        return STOP_AND_HOOK
    if not mount.hooks and ({'+x', '-x'} <= sides or {'+y', '-y'} <= sides):
        return SLIDE_RAILS
    return None


def hook_strain(hook, tolerance):
    """Root strain of a cantilever hook bent aside by its barb overlap plus `tolerance`: 1.5 t δ / L²."""
    return 1.5 * hook.thickness * (hook.overlap + tolerance) / hook.length ** 2


def board_boxes(pcb, pieces):
    """(lo, hi) of the PCB slab and every box of the board's reference pieces, and the other (solid) pieces."""
    slab = np.array([pcb.at[0] - pcb.size[0] / 2, pcb.at[1] - pcb.size[1] / 2, pcb.at[2]])
    boxes = [(slab, slab + np.array(pcb.size))]
    solids = []
    for piece in pieces:
        if isinstance(piece, Box):
            c, s = np.array(piece.center, float), np.array(piece.size, float)
            boxes.append((c - s / 2, c + s / 2))
        else:
            solids.append(wp(piece.shape).val())
    return boxes, solids


def _swept(lo, hi, direction, distance):
    a, s = int(np.flatnonzero(direction)[0]), float(direction[np.flatnonzero(direction)[0]])
    lo, hi = lo.copy(), hi.copy()
    if s > 0:
        hi[a] += distance
    else:
        lo[a] -= distance
    return lo, hi


def _crop(obstacles, lo, hi):
    pieces = [p for o in obstacles for p in o.intersect(box(lo, hi)).Solids() if p.Volume() > 1e-6]
    return cq.Compound.makeCompound(pieces) if pieces else None


def _hits(obstacle, solid):
    return obstacle is not None and solid.intersect(obstacle).Volume() > 1e-4


def travel(obstacles, pcb, pieces, direction, reach=15.0):
    """How far the board (PCB slab and reference pieces) slides along the unit axis `direction` before it touches one
    of `obstacles`; boxes are swept exactly, other pieces are found by bisection to 0.01 mm."""
    direction = np.asarray(direction, float)
    a = int(np.flatnonzero(direction)[0])
    s = float(direction[a])
    boxes, solids = board_boxes(pcb, pieces)
    lows, highs = np.min([b[0] for b in boxes], axis=0), np.max([b[1] for b in boxes], axis=0)
    for solid in solids:
        bb = solid.BoundingBox()
        lows, highs = np.minimum(lows, (bb.xmin, bb.ymin, bb.zmin)), np.maximum(highs, (bb.xmax, bb.ymax, bb.zmax))
    near = _crop(obstacles, *_swept(lows - 0.01, highs + 0.01, direction, reach))
    best = reach
    if near is None:
        return best
    for lo, hi in boxes:
        for hit in near.intersect(box(*_swept(lo, hi, direction, reach))).Solids():
            if hit.Volume() < 1e-6:
                continue
            bb = hit.BoundingBox()
            first = (bb.xmin, bb.ymin, bb.zmin)[a] - hi[a] if s > 0 else lo[a] - (bb.xmax, bb.ymax, bb.zmax)[a]
            best = min(best, max(first, 0.0))
    for solid in solids:
        if not _hits(near, solid.translate(vec(direction * best))):
            continue
        free, blocked = 0.0, best
        while blocked - free > 0.01:
            mid = (free + blocked) / 2
            free, blocked = (free, mid) if _hits(near, solid.translate(vec(direction * mid))) else (mid, blocked)
        best = free
    return float(best)


def insertion_height(shell, mount, pieces, lid_axis, heights):
    """The first lift h in `heights` by which the board leaves its seat along the held-face normal, passing only through
    its flexing hooks (and, for a front stop, the lips it tilts under), and then slides out along `lid_axis` through the
    open lid face touching nothing; None if no h works. Slide rails only slide out. Boxes are swept exactly, other
    pieces are tested every 1 mm."""
    pcb = mount.pcb
    up = np.array([0.0, 0.0, float(pcb.held)])
    out = np.asarray(lid_axis, float)
    flex = [h.solid for h in mount.hooks] + ([lip.solid for lip in mount.lips] if retention(mount) == STOP_AND_HOOK else [])
    flexing = cq.Compound.makeCompound(flex) if flex else None
    boxes, solids = board_boxes(pcb, pieces)
    bb = shell.BoundingBox()
    reach = 2 * max(bb.xlen, bb.ylen, bb.zlen)

    def blocked(lift, path, distance, through):
        moved = [(lo + up * lift, hi + up * lift) for lo, hi in boxes]
        swept = cq.Compound.makeCompound([box(*_swept(lo, hi, path, distance)) for lo, hi in moved])
        volume = swept.intersect(shell)
        if through is not None:
            volume = volume.cut(through)
        if volume.Volume() > 1e-3:
            return True
        steps = np.arange(0.0, distance + 1e-9, 1.0)
        return any(_hits(shell, solid.translate(vec(up * lift + path * t))) for solid in solids for t in steps)

    if retention(mount) == SLIDE_RAILS:
        return 0.0 if not blocked(0.0, out, reach, None) else None
    if np.allclose(out, up):
        return 0.0 if not blocked(0.0, up, reach, flexing) else None
    for h in heights:
        if not blocked(0.0, up, h, flexing) and not blocked(h, out, reach, None):
            return float(h)
    return None


def mount_report(mount, shell, lid, pieces, lid_axis):
    """Measure how `mount` holds its board in the built `shell` with the closed `lid`; returns (report, problems)."""
    pcb = mount.pcb
    kind = retention(mount)
    problems = [] if kind else ['hooks and lips do not make snap hooks, a front stop with a hook, or slide rails']
    problems += [f'hook {i} is a rigid {type(h).__name__}, not a Hook' for i, h in enumerate(mount.hooks) if not isinstance(h, Hook)]
    problems += [f'lip {i} is not a Lip' for i, lip in enumerate(mount.lips) if not isinstance(lip, Lip)]
    if problems:
        return {'retention': kind}, problems
    grips = barb_grips(shell, pcb)
    problems += grip_problems(grips)
    declared = {part.side for part in (*mount.hooks, *mount.lips)}
    problems += [f'the grip at {side} comes from no declared hook or lip' for side, _, _ in grips if side not in declared]
    problems += [f'the hook or lip at {side} grips nothing' for side in declared if side not in {g[0] for g in grips}]
    share = pcb.tolerance if kind == STOP_AND_HOOK else pcb.tolerance / 2
    strains = [hook_strain(h, share) for h in mount.hooks]
    problems += [f'hook at {h.side} bends {e:.1%} to let the board in, more than {MAX_STRAIN:.0%}'
                 for h, e in zip(mount.hooks, strains) if e > MAX_STRAIN]
    moves, worst = {}, MIN_OVERLAP * 10
    for side in IN_PLANE:
        t = travel([shell, lid], pcb, pieces, unit(side))
        moves[side] = round(t, 2)
        if t > MAX_TRAVEL:
            problems.append(f'the board slides {t:.1f} mm towards {side}, more than {MAX_TRAVEL}')
            continue
        shifted = pcb._replace(at=tuple(np.array(pcb.at) + t * unit(side)))
        moved = barb_grips(shell, shifted)
        problems += [f'after sliding {t:.2f} mm towards {side}: {p}' for p in grip_problems(moved)]
        by_side = {}
        for side_held, o, _ in moved:
            by_side[side_held] = max(o, by_side.get(side_held, 0.0))
        worst = min(worst, sorted(by_side.values())[-2] if len(by_side) >= 2 else 0.0)
    lift = insertion_height(shell, mount, pieces, lid_axis, heights=np.arange(1.6, 8.0, 0.5))
    if lift is None:
        problems.append('the board cannot get in: no lift up to 7.6 mm clears everything but its hooks')
    report = {'retention': kind,
              'grips': [{'side': side, 'overlap_mm': round(o, 2), 'gap_mm': round(g, 2)} for side, o, g in grips],
              'travel_mm': moves, 'worst_overlap_mm': round(worst, 2), 'insertion_lift_mm': lift,
              'hook_strain_pct': [round(100 * e, 2) for e in strains]}
    if kind == STOP_AND_HOOK:
        hook = mount.hooks[0]
        a = FACES[hook.side][0]
        tilt = (HOOK_GAP + HOOK_LAND + HOOK_SIDE_GAP + hook.overlap + 0.2) / pcb.size[a]
        lip_grips = [(o, g) for side, o, g in grips if side in {lip.side for lip in mount.lips}]
        report['tilt'] = round(tilt, 3)
        problems += [f'a lip {g:.2f} mm over the board is too low to tilt under: the board must rise {o * tilt:.2f} mm there'
                     for o, g in lip_grips if g < o * tilt]
    return report, problems


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


def declare(model, spec, *, color, refs=(), boards=()):
    """Register shell, lid, fasteners, references, measurements, the open-lid animation and the standard checks.

    `boards` are the Mounts of the boards the module holds with hooks and lips in `spec.adds`; with any, the board
    check is registered too."""
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

    shell_fasteners = tuple(name for name in ('magnets', 'washers') if name in groups())
    lid_fasteners = tuple(name for name in ('lidMagnets', 'lidWashers') if name in groups())
    carried_by_shell = shell_fasteners + tuple(ref_id for ref_id, _, _ in refs)

    model.part('shell', 'Thân', color=color, drag=Drag(tuple(-v for v in axis), 60, carried_by_shell),
               print_rotation=UP[spec.lid])(lambda: wp(shapes()[0]).translate(offset))
    model.part('lid', 'Nắp', color=LID_COLOR, drag=Drag(axis, 90, lid_fasteners),
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
    moving = ['lid', *lid_fasteners]
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

    if boards:
        pieces_of = {ref_id: pieces for ref_id, _, pieces in refs}

        @model.check('Boards held in place')
        def boards_held():
            report, problems = [], []
            for i, mount in enumerate(boards):
                entry, found = mount_report(mount, shapes()[0], shapes()[1], pieces_of[mount.ref], unit(spec.lid))
                report.append(entry)
                problems += [f'board {i}: {p}' for p in found]
            if problems:
                raise CheckFailed('; '.join(problems))
            return {'boards': report}


def kit_model(model_id, *, title, description, spec, color, refs=(), boards=(), notes=(), sections=()):
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
    declare(model, spec, color=color, refs=refs, boards=boards)
    return model
