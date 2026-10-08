"""ps4-wraeclast-stand: vertical stand for an original PS4 (CUH-1000A) and two DualShock 4
altars, dressed as Wraeclast ruins. Millimetres, Z up; the console front (disc slot) faces -Y.

Every shape is generated here: weathered stone, runes, a jawless skull and a broken chain. No
mesh, logo or text comes from a game. The console envelope and intake position are
assumptions; see README before printing.

Pipeline per stone part (`stone`): CadQuery blank → seeded chips → art.erode (inward only)
→ simplify → exact functional cutters last. Each part is built set-local, then placed in the
front set; the back set is the front set turned 180° about Z.
"""

import hashlib
import math
import random
from functools import cache

import cadquery as cq
import manifold3d as m3
import numpy as np
import trimesh

from printkit import Box, Drag, Model, Solid, art
from printkit.checks import CheckFailed, overlap
from printkit.export import print_frame
from printkit.pose import (
    composed_pose,
    euler_xyz_matrix,
    installed_pose,
    matrix_euler_xyz,
    tidy,
)
from printkit.shapes import block, placed

# Console on its narrow side face; front (disc slot) faces -Y.
CONSOLE, CONSOLE_Z, CONSOLE_G = (53.0, 305.0, 275.0), 20.0, 2800.0
SET_Y = 92.5
LOWER, UPPER = (170.0, 80.0, 10.0), (160.0, 72.0, 10.0)
TOP = LOWER[2] + UPPER[2]
WALL_IN, WALL_OUT, WALL_Y, WALL_TOP, WALL_MIN = 27.0, 39.0, 25.0, 65.0, 54.0
SLOT_FLOOR, RIB_Y = 6.0, (14.0, 22.0)
SOCKET, SOCKET_DEPTH, SOCKET_X = 34.4, 6.0, 60.0
FLOOR = TOP - SOCKET_DEPTH
BUMPER_D, BUMPER_H, BUMPER_XY = 12.0, 1.5, (70.0, 30.0)
SHAFT, CHAMFER, TENON_H, BAND, BAND_TOP = 34.0, 4.0, 6.0, 40.0, 18.0
TALL_H, STUB_H, BREAK_ZONE = 210.0, 100.0, 30.0
HOOK_Z, HOOK_D, HOOK_L, GUSSET_W = 170.0, 6.0, 20.0, 4.0
PEG_D, PEG_H, HOLE_D, HOLE_H = 8.0, 6.0, 8.4, 7.0
WIRE, LINK_STRAIGHT, LINK_R, LINKS, LINK_OVERLAP = 4.0, 10.0, 6.0, 7, 0.4
PITCH = LINK_STRAIGHT + 2 * LINK_R - WIRE + LINK_OVERLAP
CHAIN_X, CHAIN_GAP, BREAK_GAP = 32.0, 0.2, 2.0
# Glyph size, stroke width, groove depth.
PILLAR_GLYPH, BAND_GLYPH = (18.0, 2.0, 1.5), (8.0, 1.2, 1.0)
RUNE_Z0, RUNE_PITCH = BAND_TOP + 4, 21.0
RUNE_TOP = RUNE_Z0 + 5 * RUNE_PITCH + PILLAR_GLYPH[0]
# DualShock 4 envelope (width along Y, thickness, depth grips->top) and its altar.
# Set-local, front set, on the stub side (-X); ALTAR_EDGE is the box's back-bottom edge (x, z).
DS4, DS4_G, LEAN = (162.0, 57.0, 100.0), 210.0, 70.0
ALTAR_X, ALTAR_Y, ALTAR_SLAB, ALTAR_EDGE = (
    (-180.0, -86.0),
    (-59.0, 123.0),
    10.0,
    (-118.0, 10.2),
)
CHEEK_T, CHEEK_GAP, CHEEK_TOP, CHEEK_LOW = 8.0, 2.0, 60.0, 38.0
BACKREST_T, BACKREST_REACH, LIP_GAP, LIP_T, LIP_H, OVERFILL = (
    8.0,
    0.6,
    1.0,
    6.0,
    10.0,
    3.0,
)
SEAT_PLAY = 0.02  # seat and backrest sit this far off the envelope, so float32 contact is not overlap
DS4_Y0 = ALTAR_Y[0] + CHEEK_T + CHEEK_GAP
LEAN_V = np.array([math.cos(math.radians(LEAN)), 0.0, math.sin(math.radians(LEAN))])
LEAN_N = np.array([-math.sin(math.radians(LEAN)), 0.0, math.cos(math.radians(LEAN))])
# Joint on the bed: a tongue floating above the bed would be a 20 mm cantilever.
POCKET = (
    (-90.0, -65.0),
    (-20.0, 20.0),
    (-1.0, 5.8),
)  # cut into the plinth's -X end, open below
TONGUE = (
    (-87.0, -65.2),
    (-19.8, 19.8),
    (0.0, 5.6),
)  # altar locator, 0.2 clear of the pocket
ALTAR_BUMPERS = ((-170.0, -96.0), (-49.0, 113.0))
EROSION, CHIP_MAX = 1.0, 6.0
SEEDS = {"plinth": 11, "tall_pillar": 23, "stub": 37, "altar": 53}
PLA_G_MM3, BED, MAX_TRIS, EPS = 1.24e-3, 250.0, 60000, 1e-3
SHELL_MM, INFILL = (
    1.2,
    0.15,
)  # 3 wall loops of 0.4 mm, 15 % gyroid, for the mass estimate

# Original glyphs on a unit square, each a list of strokes.
GLYPHS = (
    (((0.5, 0), (0.5, 1)), ((0.5, 0.72), (0.12, 0.38)), ((0.5, 0.72), (0.88, 0.38))),
    (
        ((0.5, 1), (0.1, 0.5)),
        ((0.1, 0.5), (0.5, 0)),
        ((0.5, 0), (0.9, 0.5)),
        ((0.9, 0.5), (0.5, 1)),
        ((0.5, 0.42), (0.5, 0.58)),
    ),
    (
        ((0.15, 1), (0.75, 0.62)),
        ((0.75, 0.62), (0.25, 0.38)),
        ((0.25, 0.38), (0.85, 0)),
    ),
    (
        ((0.1, 0.92), (0.9, 0.92)),
        ((0.15, 0.75), (0.85, 0.05)),
        ((0.85, 0.75), (0.15, 0.05)),
    ),
    (
        ((0.5, 0.95), (0.08, 0.12)),
        ((0.08, 0.12), (0.92, 0.12)),
        ((0.92, 0.12), (0.5, 0.95)),
        ((0.5, 0.38), (0.5, 0.55)),
    ),
    (((0.3, 0), (0.3, 1)), ((0.3, 1), (0.82, 0.72)), ((0.3, 0.52), (0.78, 0.3))),
)


def column(side, z0, z1):
    return block(side, side, z1 - z0, z=z0).edges("|Z").chamfer(CHAMFER)


def bounds_block(bounds):
    """Box from ((x0, x1), (y0, y1), (z0, z1))."""
    (x0, x1), (y0, y1), (z0, z1) = bounds
    return block(x1 - x0, y1 - y0, z1 - z0, x=(x0 + x1) / 2, y=(y0 + y1) / 2, z=z0)


def cylinder_z(d, z0, z1, x=0, y=0):
    return cq.Workplane("XY", origin=(x, y, z0)).circle(d / 2).extrude(z1 - z0)


def glyph(index, plane, size, stroke, depth):
    """Groove cutter on `plane` (origin `depth` inside the face, normal pointing out)."""
    cutter = None
    for a, b in GLYPHS[index]:
        (ax, ay), (bx, by) = [
            ((u - 0.5) * (size - stroke), (v - 0.5) * (size - stroke))
            for u, v in (a, b)
        ]
        stroke_shape = (
            cq.Workplane(plane)
            .center((ax + bx) / 2, (ay + by) / 2)
            .slot2D(
                math.hypot(bx - ax, by - ay) + stroke,
                stroke,
                math.degrees(math.atan2(by - ay, bx - ax)),
            )
            .extrude(depth + 1)
        )
        cutter = stroke_shape if cutter is None else cutter.union(stroke_shape)
    return cutter


def wedge(depth, rise, fall, width, roll):
    """V-shaped chip, apex line `depth` inside a face whose outward normal is +X.

    `rise` and `fall` are the arm angles from the face normal, in degrees; an
    upper arm of 45 deg or more leaves a self-supporting overhang.
    """
    arms = [
        (6, sign * (depth + 6) * math.tan(math.radians(a)))
        for a, sign in ((rise, 1), (fall, -1))
    ]
    return (
        cq.Workplane("XZ")
        .polyline([(-depth, 0)] + arms)
        .close()
        .extrude(width / 2, both=True)
        .rotate((0, 0, 0), (1, 0, 0), roll)
    )


def union_all(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.union(shape)
    return result


# ---------------------------------------------------------------- plinth


def wall_breaks(rng):
    """Broken wall tops: every cut stays above WALL_MIN, so the cradle keeps its grip."""
    cuts = []
    for side in (-1, 1):
        region = block(
            WALL_OUT - WALL_IN + 4,
            2 * WALL_Y + 4,
            60,
            x=side * (WALL_IN + WALL_OUT) / 2,
            z=WALL_MIN,
        )
        end = rng.choice((-1, 1))
        drop = rng.uniform(WALL_MIN + 1, WALL_TOP - 4)
        slope = rng.uniform(6, 14)
        plane = (
            block(80, 120, 80)
            .rotate((0, 0, 0), (1, 0, 0), -end * slope)
            .translate((side * (WALL_IN + WALL_OUT) / 2, end * WALL_Y, drop))
        )
        cuts.append(plane.intersect(region))
        notch_z = rng.uniform(WALL_MIN + 1, WALL_TOP - 5)
        notch = (
            wedge(
                WALL_TOP - notch_z + 1, rng.uniform(35, 50), rng.uniform(35, 50), 24, 0
            )
            .rotate((0, 0, 0), (0, 1, 0), -90)
            .rotate((0, 0, 0), (0, 0, 1), 90)
            .translate(
                (side * (WALL_IN + WALL_OUT) / 2, rng.uniform(-14, 14), WALL_TOP + 1)
            )
        )
        cuts.append(notch.intersect(region))
        for _ in range(2):
            chip = (
                block(10, rng.uniform(8, 14), 10)
                .rotate((0, 0, 0), (0, 1, 0), side * rng.uniform(35, 55))
                .translate(
                    (
                        side * (WALL_OUT + 2.5),
                        rng.uniform(-20, 20),
                        WALL_TOP - rng.uniform(1.5, 3.5),
                    )
                )
            )
            cuts.append(chip.intersect(region))
    return cuts


@cache
def plinth_blank():
    body = block(*LOWER).union(block(*UPPER, z=LOWER[2]))
    body = body.union(block(2 * WALL_OUT, 2 * WALL_Y, WALL_TOP - TOP, z=TOP))
    for cut in wall_breaks(random.Random(SEEDS["plinth"])):
        body = body.cut(cut)
    return body.clean()


@cache
def plinth_cutters():
    slot = block(2 * WALL_IN, LOWER[1] + 20, 100, z=SLOT_FLOOR)
    for y in (-1, 1):
        rib = block(
            2 * WALL_IN + 2,
            RIB_Y[1] - RIB_Y[0],
            TOP - SLOT_FLOOR + 1,
            y=y * sum(RIB_Y) / 2,
            z=SLOT_FLOOR - 1,
        )
        slot = slot.cut(rib)
    cutters = [slot, bounds_block(POCKET)]
    cutters += [
        block(SOCKET, SOCKET, SOCKET_DEPTH + 5, x=x, z=FLOOR)
        for x in (-SOCKET_X, SOCKET_X)
    ]
    cutters += [
        cylinder_z(BUMPER_D, -1, BUMPER_H, x * BUMPER_XY[0], y * BUMPER_XY[1])
        for x in (-1, 1)
        for y in (-1, 1)
    ]
    size, stroke, depth = BAND_GLYPH
    order = (0, 1, 2, 3, 4, 5, 2, 4, 1, 3)
    for i, x in enumerate(
        [35 + 10.5 * k for k in range(5)] + [-35 - 10.5 * k for k in range(5)]
    ):
        cutters.append(
            glyph(
                order[i],
                cq.Plane.named("XZ", (x, -LOWER[1] / 2 + depth, LOWER[2] / 2)),
                size,
                stroke,
                depth,
            )
        )
    return union_all(cutters)


PLINTH_MASK = (
    (
        (-LOWER[0] / 2 - 5, -LOWER[1] / 2 - 1, -1),
        (LOWER[0] / 2 + 5, -LOWER[1] / 2 + 1.5, LOWER[2] + 0.5),
    ),
)


# ---------------------------------------------------------------- columns


def corner_chips(rng, count, z_range, shallow_zone):
    """Wedge chips on the vertical chamfer faces; depth is exact (apex line parallel to the face)."""
    distance = (SHAFT - CHAMFER) / math.sqrt(2)
    chips, placed = [], []
    while len(chips) < count:
        corner = rng.choice(((1, 1), (1, -1), (-1, -1), (-1, 1)))
        z = rng.uniform(*z_range)
        above = (shallow_zone[1] + 12, z_range[1])
        if (
            (corner[0] == 1 or corner[1] == -1)
            and above[0] < above[1]
            and rng.random() < 0.5
        ):
            z = rng.uniform(*above)
        if any(c == corner and abs(z - zc) < 16 for c, zc in placed):
            continue
        near_rune = (corner[0] == 1 or corner[1] == -1) and shallow_zone[
            0
        ] - 12 < z < shallow_zone[1] + 12
        depth = rng.uniform(1.5, 2.5) if near_rune else rng.uniform(3, CHIP_MAX)
        azimuth = math.degrees(math.atan2(corner[1], corner[0]))
        chip = (
            wedge(
                depth,
                rng.uniform(46, 60),
                rng.uniform(30, 55),
                16,
                rng.uniform(-25, 25),
            )
            .rotate((0, 0, 0), (0, 0, 1), azimuth)
            .translate(
                (
                    distance * math.cos(math.radians(azimuth)),
                    distance * math.sin(math.radians(azimuth)),
                    z,
                )
            )
        )
        chips.append((chip, depth))
        placed.append((corner, z))
    return chips


def broken_top(rng, height):
    """3-5 cuts inside the top BREAK_ZONE mm.

    Slanted planes fall away from one surviving peak corner; a V-notch splits
    the top into horns.
    """
    peak = rng.uniform(0, 360)
    count = rng.randint(3, 5)
    cuts = []
    for _ in range(count - 1):
        azimuth, tilt = peak + 180 + rng.uniform(-80, 80), rng.uniform(25, 42)
        low = height - rng.uniform(10, BREAK_ZONE - 5)
        plane = (
            block(200, 200, 200)
            .rotate((0, 0, 0), (0, 1, 0), tilt)
            .rotate((0, 0, 0), (0, 0, 1), azimuth)
            .translate(
                (
                    SHAFT / 2 * math.cos(math.radians(azimuth)),
                    SHAFT / 2 * math.sin(math.radians(azimuth)),
                    low,
                )
            )
        )
        cuts.append(plane)
    apex = height - rng.uniform(10, 18)
    notch = (
        wedge(height - apex + 5, rng.uniform(22, 32), rng.uniform(22, 32), 80, 0)
        .rotate((0, 0, 0), (0, 1, 0), -90)
        .rotate((0, 0, 0), (0, 0, 1), rng.uniform(0, 180))
        .translate((rng.uniform(-5, 5), rng.uniform(-5, 5), height + 5))
    )
    cuts.append(notch)
    return cuts


def column_blank(height):
    """Shaft and base band from the top of the tenon up; the exact tenon is added after erosion."""
    shaft = column(SHAFT, TENON_H, height)
    band = column(BAND, TENON_H, BAND_TOP).faces("<Z").chamfer(2).faces(">Z").chamfer(2)
    return shaft.union(band)


def tenon():
    return column(SHAFT, 0, TENON_H + 0.5)


@cache
def tall_pillar_blank():
    """Returns the blank, the chip depths and the lowest point the broken top reaches."""
    rng = random.Random(SEEDS["tall_pillar"])
    column = column_blank(TALL_H)
    for _ in range(20):  # resample until one horn keeps (almost) the full height
        body = column
        for cut in broken_top(rng, TALL_H):
            body = body.cut(cut)
        if body.val().BoundingBox().zmax >= TALL_H - 4:
            break
    else:
        raise AssertionError("broken top never keeps a peak")
    lowest_cut = column.cut(body).val().BoundingBox().zmin
    chips = corner_chips(
        rng,
        rng.randint(5, 8),
        (BAND_TOP + 12, TALL_H - BREAK_ZONE - 6),
        (RUNE_Z0, RUNE_TOP),
    )
    for chip, _ in chips:
        body = body.cut(chip)
    return body.clean(), [depth for _, depth in chips], lowest_cut


def hook():
    peg = (
        cq.Workplane("YZ", origin=(SHAFT / 2 - 2, 0, HOOK_Z))
        .circle(HOOK_D / 2)
        .extrude(HOOK_L + 2)
        .faces(">X")
        .chamfer(0.5)
    )
    top = HOOK_Z - HOOK_D / 2 + 1.5
    gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (SHAFT / 2 - 2, top),
                (SHAFT / 2 + HOOK_L, top),
                (SHAFT / 2 - 2, top - HOOK_L - 2),
            ]
        )
        .close()
        .extrude(GUSSET_W / 2, both=True)
    )
    return peg.union(gusset)


@cache
def pillar_runes():
    size, stroke, depth = PILLAR_GLYPH
    cutters = []
    for i, (east, south) in enumerate(zip((0, 1, 2, 3, 4, 5), (3, 5, 1, 4, 0, 2))):
        z = RUNE_Z0 + size / 2 + i * RUNE_PITCH
        cutters.append(
            glyph(
                east,
                cq.Plane.named("YZ", (SHAFT / 2 - depth, 0, z)),
                size,
                stroke,
                depth,
            )
        )
        cutters.append(
            glyph(
                south,
                cq.Plane.named("XZ", (0, -SHAFT / 2 + depth, z)),
                size,
                stroke,
                depth,
            )
        )
    return union_all(cutters)


TENON_MASK = (
    (-BAND / 2 - 2, -BAND / 2 - 2, -1),
    (BAND / 2 + 2, BAND / 2 + 2, TENON_H + 0.5),
)
TALL_MASK = (
    TENON_MASK,
    ((SHAFT / 2 - 1, -11.5, RUNE_Z0 - 2), (SHAFT / 2 + 1, 11.5, HOOK_Z + 6)),
    ((-11.5, -SHAFT / 2 - 1, RUNE_Z0 - 2), (11.5, -SHAFT / 2 + 1, RUNE_TOP + 2)),
)
STUB_MASK = (TENON_MASK,)
SEAT_SPARE = 2.0  # blank stands this far above the seat; the exact trim removes it


@cache
def stub_blank():
    rng = random.Random(SEEDS["stub"])
    body = column_blank(STUB_H + SEAT_SPARE)
    count = rng.randint(3, 5)
    for i in range(count):
        if i % 2 == 0:
            chip = corner_chips(rng, 1, (STUB_H - 2, STUB_H + 1), (0, 0))[0][0]
        else:
            azimuth = rng.choice((0, 90, 180, 270))
            chip = (
                wedge(
                    rng.uniform(2.5, 4.5),
                    75,
                    rng.uniform(35, 50),
                    rng.uniform(8, 14),
                    rng.uniform(-12, 12),
                )
                .rotate((0, 0, 0), (0, 0, 1), azimuth)
                .translate(
                    (
                        SHAFT / 2 * math.cos(math.radians(azimuth))
                        + rng.uniform(-6, 6) * math.sin(math.radians(azimuth)),
                        SHAFT / 2 * math.sin(math.radians(azimuth))
                        + rng.uniform(-6, 6) * math.cos(math.radians(azimuth)),
                        STUB_H,
                    )
                )
            )
        body = body.cut(chip)
    return body.clean()


def stub_peg():
    return cylinder_z(PEG_D, STUB_H - 1, STUB_H + PEG_H).faces(">Z").chamfer(0.6)


# ---------------------------------------------------------------- altar


def lean_point(b, c):
    """(x, z) of the point b along v (grips -> top) and c along n (back -> face)
    from the controller's back-bottom edge."""
    x, _, z = np.array([ALTAR_EDGE[0], 0, ALTAR_EDGE[1]]) + b * LEAN_V + c * LEAN_N
    return float(x), float(z)


def lean_prism(outline, y0, y1):
    """Extrude an x-z outline along Y from y0 to y1."""
    return (
        cq.Workplane("XZ", origin=(0, y1, 0)).polyline(outline).close().extrude(y1 - y0)
    )


def cheek_breaks(rng):
    """Jagged cheek tops: a flat cap at CHEEK_TOP, a slanted break, a V-notch and two
    corner chips per cheek; nothing is cut below CHEEK_LOW except the chips."""
    cuts = []
    span_x = (ALTAR_X[0] - 1, ALTAR_X[1] + 1)
    for side, (y0, y1) in (
        (-1, (ALTAR_Y[0] - 1, ALTAR_Y[0] + CHEEK_T)),
        (1, (ALTAR_Y[1] - CHEEK_T, ALTAR_Y[1] + 1)),
    ):
        region = bounds_block((span_x, (y0, y1), (CHEEK_LOW, 200)))
        cuts.append(bounds_block((span_x, (y0, y1), (CHEEK_TOP, 200))))
        end = rng.choice((-1, 1))
        x_end = ALTAR_X[1] - 4 if end == 1 else ALTAR_X[0] + 2
        plane = (
            block(300, 60, 200)
            .rotate((0, 0, 0), (0, 1, 0), end * rng.uniform(10, 22))
            .translate(
                (x_end, (y0 + y1) / 2, rng.uniform(CHEEK_LOW + 4, CHEEK_TOP - 6))
            )
        )
        cuts.append(plane.intersect(region))
        notch_z = rng.uniform(CHEEK_LOW + 2, CHEEK_TOP - 8)
        notch = (
            wedge(
                CHEEK_TOP - notch_z + 1, rng.uniform(25, 40), rng.uniform(25, 40), 20, 0
            )
            .rotate((0, 0, 0), (0, 1, 0), -90)
            .translate(
                (
                    rng.uniform(ALTAR_X[0] + 20, ALTAR_X[1] - 20),
                    (y0 + y1) / 2,
                    CHEEK_TOP + 1,
                )
            )
        )
        cuts.append(notch.intersect(region))
        corner = (ALTAR_X[0] + 2, ALTAR_Y[0] if side < 0 else ALTAR_Y[1])
        for _ in range(2):
            chip = (
                wedge(
                    rng.uniform(3, 5),
                    rng.uniform(46, 60),
                    rng.uniform(30, 50),
                    12,
                    rng.uniform(-20, 20),
                )
                .rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(side, -1)))
                .translate((*corner, rng.uniform(16, CHEEK_LOW - 6)))
            )
            cuts.append(
                chip.intersect(bounds_block((span_x, (y0, y1), (ALTAR_SLAB + 2, 200))))
            )
    return cuts


@cache
def altar_blank():
    """Slab, cradle and cheeks. The cradle outline overfills OVERFILL mm into the
    controller pocket and over the lip's top and outer face; altar_cutters removes
    that after erosion, leaving the seat, backrest and every lip face exact."""
    rng = random.Random(SEEDS["altar"])
    lip_in, lip_out = DS4[1] + LIP_GAP, DS4[1] + LIP_GAP + LIP_T
    reach = BACKREST_REACH * DS4[2]
    outline = [
        (lean_point(0, lip_out)[0], ALTAR_SLAB - 3),
        (lean_point(0, -BACKREST_T)[0], ALTAR_SLAB - 3),
        lean_point(0, -BACKREST_T),
        lean_point(reach, -BACKREST_T),
        lean_point(reach, OVERFILL),
        lean_point(OVERFILL, lip_in - OVERFILL),
        lean_point(LIP_H + OVERFILL, lip_in - OVERFILL),
        lean_point(LIP_H + OVERFILL, lip_out + OVERFILL),
        lean_point(0, lip_out + OVERFILL),
        lean_point(0, lip_out),
    ]
    # Between the cheeks only, so the cutter removes all the overfill.
    cradle = lean_prism(outline, DS4_Y0 - CHEEK_GAP, DS4_Y0 + DS4[0] + CHEEK_GAP)
    slab = bounds_block((ALTAR_X, ALTAR_Y, (0, ALTAR_SLAB)))
    cheeks = [
        bounds_block(
            ((ALTAR_X[0] + 1.5, ALTAR_X[1] - 3.5), y_span, (0, CHEEK_TOP + 10))
        )
        for y_span in (
            (ALTAR_Y[0], ALTAR_Y[0] + CHEEK_T),
            (ALTAR_Y[1] - CHEEK_T, ALTAR_Y[1]),
        )
    ]
    body = union_all([slab, cradle, *cheeks])
    for cut in cheek_breaks(rng):
        body = body.cut(cut)
    return body.clean()


@cache
def altar_cutters():
    """Exact faces cut after erosion: seat, backrest, the lip's inner, top and outer
    faces, rune band and bumper recesses. Material with c >= lip_out exists only in
    the lip overfill, so the cutter can run past it freely."""
    lip_in, lip_out = DS4[1] + LIP_GAP, DS4[1] + LIP_GAP + LIP_T
    far = lip_out + 50
    pocket = lean_prism(
        [
            lean_point(-SEAT_PLAY, -SEAT_PLAY),
            lean_point(-SEAT_PLAY, lip_in),
            lean_point(LIP_H, lip_in),
            lean_point(LIP_H, lip_out),
            lean_point(0, lip_out),
            lean_point(0, far),
            lean_point(400, far),
            lean_point(400, -SEAT_PLAY),
        ],
        DS4_Y0 - CHEEK_GAP - 0.01,  # 0.01 into the cheek faces: no coplanar boolean
        DS4_Y0 + DS4[0] + CHEEK_GAP + 0.01,
    )
    cutters = [pocket]
    cutters += [
        cylinder_z(BUMPER_D, -1, BUMPER_H, x, y)
        for x in ALTAR_BUMPERS[0]
        for y in ALTAR_BUMPERS[1]
    ]
    size, stroke, depth = BAND_GLYPH
    count = 10
    for i in range(count):
        y = DS4_Y0 - 1 + i * (DS4[0] + 2) / (count - 1)
        plane = cq.Plane(
            origin=(ALTAR_X[0] + depth, y, ALTAR_SLAB / 2),
            xDir=(0, -1, 0),
            normal=(-1, 0, 0),
        )
        cutters.append(glyph((i * 5) % 6, plane, size, stroke, depth))
    return union_all(cutters)


ALTAR_MASK = (
    (
        (ALTAR_X[0] - 1, ALTAR_Y[0] - 5, -1),
        (ALTAR_X[0] + 1.5, ALTAR_Y[1] + 5, ALTAR_SLAB + 0.5),
    ),
    # Cheek faces toward the controller: hidden behind it, kept flat to save triangles.
    (
        (ALTAR_X[0], DS4_Y0 - CHEEK_GAP - 1, ALTAR_SLAB),
        (ALTAR_X[1], DS4_Y0 - CHEEK_GAP + 0.5, CHEEK_TOP + 1),
    ),
    (
        (ALTAR_X[0], DS4_Y0 + DS4[0] + CHEEK_GAP - 0.5, ALTAR_SLAB),
        (ALTAR_X[1], DS4_Y0 + DS4[0] + CHEEK_GAP + 1, CHEEK_TOP + 1),
    ),
)


def ds4_centre():
    """Set-local centre of the controller envelope."""
    return (
        np.array([ALTAR_EDGE[0], DS4_Y0 + DS4[0] / 2, ALTAR_EDGE[1]])
        + DS4[2] / 2 * LEAN_V
        + DS4[1] / 2 * LEAN_N
    )


# ---------------------------------------------------------------- chain


def chain_link():
    s, r = LINK_STRAIGHT / 2, LINK_R
    path = (
        cq.Workplane("XY")
        .moveTo(-s, -r)
        .lineTo(s, -r)
        .threePointArc((s + r, 0), (s, r))
        .lineTo(-s, r)
        .threePointArc((-s - r, 0), (-s, -r))
        .close()
    )
    return (
        cq.Workplane("YZ", origin=(-s, -r, 0))
        .circle(WIRE / 2)
        .sweep(path, transition="round")
    )


@cache
def chain_print():
    """Print frame: chain axis along +X from the top link, links alternate at +/-45 deg."""
    links = []
    for i in range(LINKS):
        link = chain_link()
        if i == LINKS - 1:  # broken last link
            link = link.cut(
                block(BREAK_GAP, WIRE + 2, WIRE + 2, y=LINK_R, z=-(WIRE + 2) / 2)
            )
        links.append(
            link.rotate((0, 0, 0), (1, 0, 0), 45 if i % 2 == 0 else -45).translate(
                (i * PITCH, 0, 0)
            )
        )
    chain = union_all(links)
    box = chain.val().BoundingBox()
    shift = (-(box.xmin + box.xmax) / 2, -(box.ymin + box.ymax) / 2, -box.zmin)
    return chain.translate(shift), shift


# ---------------------------------------------------------------- skull (SDF)
# Teeth sit on an arc around (0, TEETH_ARC_Y); the face looks toward -Y.
TEETH_ARC_Y, TEETH_ARC_R, TEETH = -9.0, 13.0, 8
TEETH_ANGLES = [math.radians(-52 + 104 * i / (TEETH - 1)) for i in range(TEETH)]


def skull_distance(p):
    """Jawless stylised skull, facing -Y; negative inside. The base plane z = 0 is trimmed by skull()."""
    x, y, z = p
    ax = abs(x)  # bilateral symmetry
    q = (ax, y, z)
    d = art.ellipsoid(q, (0, 6, 25), (20, 23.5, 21.5))  # cranium
    d = art.smin(
        d, art.round_box((ax, y - 4, z - 5.5), (15, 17, 5.5), 3), 10
    )  # flat base
    d = art.smin(
        d, art.round_box((ax, y + 13, z - 18), (15, 9, 10), 5), 6
    )  # face block
    d = art.smin(d, art.round_box((ax, y + 15, z - 6), (11, 7, 6), 3), 3)  # maxilla
    d = art.smin(d, art.ellipsoid(q, (14.5, -15, 15), (6, 6, 4)), 4)  # cheekbone
    d = art.smin(
        d, art.capsule(q, (15, -12, 15), (17.5, 6, 15.5), 2.5), 3
    )  # zygomatic arch
    d = art.smin(d, art.ellipsoid(q, (0, -19, 27), (17, 4.5, 4)), 5)  # brow ridge
    d = art.smax(d, -art.ellipsoid(q, (21, -2, 23), (3.5, 8, 7)), 3)  # temple
    d = art.smax(d, -art.ellipsoid(q, (9.5, -25, 20.5), (6.3, 11, 5.8)), 1.5)  # orbit
    nose = art.triangle_2d(ax, z, (2.8, 14.8), (-2.8, 14.8), (0, 8.2)) - 0.9
    d = art.smax(d, -max(nose, y + 16, -30 - y), 1.5)  # nasal aperture
    if z < 9 and y < 4:
        for angle in TEETH_ANGLES:
            s, c = math.sin(angle), math.cos(angle)
            cx, cy = TEETH_ARC_R * s, TEETH_ARC_Y - TEETH_ARC_R * c
            dx, dy = x - cx, y - cy
            # Tooth frame: u along the arc, v radial (outward), w vertical.
            u, v = dx * c + dy * s, dx * s - dy * c
            d = art.smin(d, art.round_box((u, v, z - 3.2), (1.35, 1.8, 3.2), 0.6), 0.5)
    return d


@cache
def skull_local():
    """Skull on its exact flat base at z = 0, with the peg hole."""
    shape = art.level_set(
        skull_distance, (-24.0, -28.0, -1.5, 24.0, 32.0, 49.0), art.MESH_EDGE
    )
    shape = shape.trim_by_plane((0.0, 0.0, 1.0), 0.0).simplify(art.SIMPLIFY_TOL)
    return shape - art.to_manifold(cylinder_z(HOLE_D, -1, HOLE_H))


# ---------------------------------------------------------------- stone pipeline


def stone(blank, seed, mask, exact_add=None, cutters=None, ceiling=None):
    """Erode the blank, simplify, then restore exact functional geometry.

    Returns the part and the volume the erosion step alone left outside the blank."""
    core = art.to_manifold(blank)
    eroded = art.erode(core, seed, EROSION, mask)
    outward = (eroded - core).volume()
    shape = eroded.simplify(art.SIMPLIFY_TOL)
    if ceiling is not None:  # exact flat top: keep z <= ceiling
        shape = shape.trim_by_plane((0.0, 0.0, -1.0), -ceiling)
    if exact_add is not None:
        shape = shape + art.to_manifold(exact_add)
    if cutters is not None:
        shape = shape - art.to_manifold(cutters)
    return shape, outward


@cache
def stones():
    """Set-local printable stone parts: name -> (Manifold, erosion-step volume outside the blank)."""
    tall_core = tall_pillar_blank()[0]
    return {
        "plinth": stone(
            plinth_blank(), SEEDS["plinth"], PLINTH_MASK, cutters=plinth_cutters()
        ),
        "pillar": stone(
            tall_core,
            SEEDS["tall_pillar"],
            TALL_MASK,
            tenon().union(hook()),
            pillar_runes(),
        ),
        "stub": stone(
            stub_blank(),
            SEEDS["stub"],
            STUB_MASK,
            tenon().union(stub_peg()),
            ceiling=STUB_H,
        ),
        "altar": stone(
            altar_blank(),
            SEEDS["altar"],
            ALTAR_MASK,
            bounds_block(TONGUE),
            altar_cutters(),
        ),
    }


@cache
def cores():
    """Set-local mechanical cores: the stone parts before erosion, and the chain. Exported as the STEP."""
    return {
        "plinth": plinth_blank().cut(plinth_cutters()),
        "pillar": tall_pillar_blank()[0]
        .union(tenon().union(hook()))
        .cut(pillar_runes()),
        "stub": stub_blank()
        .cut(block(4 * BAND, 4 * BAND, 2 * SEAT_SPARE, z=STUB_H))
        .union(tenon().union(stub_peg())),
        "altar": altar_blank().cut(altar_cutters()).union(bounds_block(TONGUE)),
    }


# Chain: print frame has the chain axis along +X; hanging, the axis points down and the top
# link plane is YZ. CHAIN_TILT turns the print frame into the hanging frame.
CHAIN_TILT = (-90.0, 45.0, 90.0)
CHAIN_PRINT = tuple(tidy(matrix_euler_xyz(euler_xyz_matrix(CHAIN_TILT).T)))


@cache
def chain_print_mesh():
    """Print-frame chain mesh with its lowest vertex on the bed, and the matching shift of the BRep."""
    chain_core, shift = chain_print()
    chain = art.to_manifold(chain_core, 0.05, 0.3)
    lift = chain.bounding_box()[2]  # tessellation is inscribed
    return (
        chain.translate((0, 0, -lift)),
        chain_core.translate((0, 0, -lift)),
        (shift[0], shift[1], shift[2] - lift),
    )


def chain_position():
    """Set-local position of the chain's print frame when it hangs on the hook."""
    top_link = np.array(
        [
            CHAIN_X,
            0,
            HOOK_Z + HOOK_D / 2 + CHAIN_GAP - (LINK_STRAIGHT / 2 + LINK_R - WIRE / 2),
        ]
    )
    shift = np.array(chain_print_mesh()[2])
    return tuple(
        np.array([SOCKET_X, 0, FLOOR]) + top_link - euler_xyz_matrix(CHAIN_TILT) @ shift
    )


# Set-local placement of each part kind (rotation, position), then the front set's offset.
LOCAL = {
    "plinth": ((0, 0, 0), (0, 0, 0)),
    "pillar": ((0, 0, 0), (SOCKET_X, 0, FLOOR)),
    "stub": ((0, 0, 0), (-SOCKET_X, 0, FLOOR)),
    "skull": ((0, 0, 0), (-SOCKET_X, 0, FLOOR + STUB_H)),
    "altar": ((0, 0, 0), (0, 0, 0)),
}
FRONT, BACK = (0, -SET_Y, 0), (0, 0, 180)


def front(shape, kind):
    rotation, position = LOCAL[kind]
    return placed(placed(shape, rotation, position), (0, 0, 0), FRONT)


def front_chain(shape):
    return placed(placed(shape, CHAIN_TILT, chain_position()), (0, 0, 0), FRONT)


# ---------------------------------------------------------------- model

STONE, BONE, IRON = "#7a746b", "#d9cfb4", "#3d3d42"
LEAN_LIFT = tuple(65 * LEAN_V)

model = Model(
    "ps4-wraeclast-stand",
    title="PS4 · Phế tích Wraeclast",
    description="Giá dựng đứng PS4 đời đầu và hai bệ tay cầm: cột khắc rune, sọ, xích gãy. Mọi hình khối sinh từ code.",
    category="Giá đỡ",
    status="Chưa in thử",
    thumbnail="thumbnail.png",
    dimensions=(360.0, 305.0, 295.0),
    camera={
        "position": [620, -880, 540],
        "target": [0, -10, 120],
        "minDistance": 150,
        "maxDistance": 1900,
    },
    grid={"size": 500, "divisions": 50},
    print_info={
        "summary": "≈ 907 g PLA cho 2 bộ, 2 bệ tay cầm và coupon · in coupon trước · chưa in thử",
        "sections": [
            {
                "title": "Thứ tự in",
                "rows": [
                    [
                        "1. Coupon thử khe",
                        "fitCoupon.stl · một lát của đế, ≈ 15–25 phút",
                    ],
                    ["2. Đế", "plinth.stl · in 2 cái"],
                    ["3. Cột", "pillar.stl ×2, stub.stl ×2"],
                    ["4. Trang trí", "skull.stl ×2, chain.stl ×2 · cần support"],
                    ["5. Bệ tay cầm", "altar.stl ×2 · không cần support"],
                ],
                "notes": [
                    "Lắp coupon lên máy thật trước: máy phải lọt khe 54 mm và nằm trên gân đỡ. Chỉnh máy in nếu quá chặt hoặc quá lỏng; không scale STL.",
                    "Hai bộ dùng chung STL; bộ sau xoay 180° quanh trục đứng nên cột cao nằm chéo góc.",
                    "Bệ tay cầm đứng riêng trên 4 chân cao su. Mộng 39,6 × 19,8 × 5,6 mm cắm vào hốc dưới đầu −X của đế (hở 0,2 mm) chỉ để định vị, không chịu lực.",
                ],
                "links": [],
            },
            {
                "title": "Cấu hình in thử",
                "rows": [
                    ["Máy / vật liệu", "Bambu A1 / P1S / X1C · nozzle 0,4 mm · PLA"],
                    ["Layer / lớp đầu", "0,20 / 0,20 mm"],
                    ["Thành", "Arachne · 3 wall loops"],
                    ["Lớp đặc trên / dưới", "5 / 4"],
                    ["Infill", "15% Gyroid"],
                    ["Support", "Đế, cột, bệ, coupon: tắt · Sọ, xích: tree"],
                    ["Brim", "Cột cao: 5 mm · còn lại tắt"],
                    ["Scale / đơn vị", "100% / mm"],
                    ["Bù lỗ / biên XY", "0 / 0 mm"],
                    ["Nhiệt, quạt, flow, bù chân voi", "Theo preset nhựa và bàn in"],
                ],
                "notes": [
                    "Hướng in giữ nguyên như trong file: đế, cột, bệ tay cầm, coupon đáy xuống bàn; sọ đáy phẳng xuống bàn; xích nằm ngang, các mắt nghiêng ±45°.",
                    "Móc treo xích có gân 45° bên dưới nên cột cao in đứng không cần support.",
                    "Hõm chân cao su Ø12 × 1,5 mm ở mặt dưới đế là cầu 12 mm. Nếu võng, chỉ bật support cho vùng đó.",
                    "Sọ: support cho hốc mắt, gò má và hàng răng. Xích: support cho nửa trên mỗi mắt; gỡ nhẹ tay vì dây Ø4 mm.",
                    "Bệ tay cầm: xem gờ chặn dày 6 mm và rãnh rune trong Preview. Hốc mộng ở đầu −X của đế là cầu rộng 40 mm.",
                ],
                "links": [
                    {
                        "label": "Arachne",
                        "url": "https://wiki.bambulab.com/en/software/bambu-studio/wall-generator",
                    },
                    {
                        "label": "Bù chân voi",
                        "url": "https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot",
                    },
                ],
            },
            {
                "title": "Nhựa & chi phí",
                "rows": [
                    ["Đế ×2", "2 × 109,2 g"],
                    ["Cột cao ×2", "2 × 78,4 g"],
                    ["Cột gãy ×2", "2 × 40,5 g"],
                    ["Sọ ×2", "2 × 22,0 g"],
                    ["Xích ×2", "2 × 6,2 g"],
                    ["Bệ tay cầm ×2", "2 × 186,5 g"],
                    ["Coupon thử khe", "21,8 g"],
                    ["Tổng 2 bộ + 2 bệ + coupon", "≈ 907 g"],
                    ["Nếu in đặc 100% (cùng số chi tiết)", "2.647 g"],
                ],
                "notes": [
                    "Mọi số tính cho 2 bộ, 2 bệ tay cầm và 1 coupon. Ước tính từ thể tích và diện tích bề mặt CAD: vỏ 1,2 mm (3 thành) cộng 15% infill, PLA 1,24 g/cm³. Support, brim và nhựa mồi cộng thêm.",
                    "Ví dụ cuộn 300.000đ/kg: khoảng 272.000đ cho cùng số chi tiết, chưa tính điện và in lỗi. Bambu Studio cho số chính xác sau khi Slice.",
                ],
                "links": [
                    {
                        "label": "PLA 1,24 g/cm³",
                        "url": "https://store.bblcdn.com/s7/default/b189de92249a4b9ebed28b8ea1f080f0/Bambu_PLA_Basic_Technical_Data_Sheet.pdf",
                    }
                ],
            },
            {
                "title": "Độ vừa",
                "rows": [],
                "notes": [
                    "Máy giả định: PS4 đời đầu CUH-1000A, 275 × 53 × 305 mm, 2,8 kg. Không dành cho PS4 Slim hoặc Pro.",
                    "Khe 54 mm, hở 0,5 mm mỗi bên. Máy tựa trên 4 gân đỡ; gầm máy cách bàn 20 mm, rãnh gió đáy cao 14 mm chạy suốt chiều sâu đế.",
                    "Hai cụm đế chỉ chiếm y = ±52,5…132,5 mm nên không che cổng trước, cổng sau và lỗ thoát nhiệt. Bệ tay cầm đặt cạnh máy (x = ±86…180 mm), cách vùng cổng 1 mm. Vị trí lưới hút gió ở hai mặt hông chưa đo trên máy thật.",
                    "Cột cắm hốc 34,4 mm (chân cột 34 mm, sâu 6 mm). Chốt Ø8 × 6 mm của cột gãy vào lỗ Ø8,4 × 7 mm dưới sọ.",
                    "Góc lật tối thiểu 23,96° kể cả khi bỏ qua khối lượng giá (30,07° với PLA đặc và 2 tay cầm), tính tới tâm 4 chân cao su mỗi đế. Bệ tay cầm không gắn cứng nên không được tính vào đa giác đỡ.",
                    "7 STL kín, mỗi file một khối, dưới 60.000 tam giác. STEP chỉ chứa phần cơ khí của 10 chi tiết in (chưa bào mòn, không có sọ).",
                    "Tay cầm giả định: DualShock 4, hộp bao 162 × 57 × 100 mm, 210 g (số công bố dao động 161–162 × 52–57 × 98–100 mm). Bệ chỉ dựa trên hộp bao này, không theo đường cong thật của tay cầm.",
                    "Tay cầm nghiêng 70°, mặt hướng ra ngoài, đầu (cổng micro-USB) hướng về đế; lưng tựa chỉ cao 60% chiều dài nên cổng sạc vẫn thông. Hai má hở 2 mm, gờ chặn trước hở 1 mm.",
                    "Lấy tay cầm: nhấc lên khỏi gờ chặn rồi kéo ra phía ngoài. Nhấc thẳng theo trục nghiêng chỉ được 19 mm rồi chạm sọ.",
                    "Chưa in thử, chưa thử tải trọng.",
                ],
                "links": [],
            },
        ],
    },
)


@model.part(
    "plinth",
    "Đế trước",
    color=STONE,
    drag=Drag((0, 0, -1), 60),
    core=lambda: front(cores()["plinth"], "plinth"),
)
def plinth():
    return front(stones()["plinth"][0], "plinth")


plinth_back = model.copy(
    "plinthBack", "Đế sau", of="plinth", rotation=BACK, drag=Drag((0, 0, -1), 60)
)


@model.part(
    "pillar",
    "Cột cao trước",
    color=STONE,
    drag=Drag((0, 0, 1), 150),
    core=lambda: front(cores()["pillar"], "pillar"),
)
def pillar():
    return front(stones()["pillar"][0], "pillar")


pillar_back = model.copy(
    "pillarBack", "Cột cao sau", of="pillar", rotation=BACK, drag=Drag((0, 0, 1), 150)
)


@model.part(
    "stub",
    "Cột gãy trước",
    color=STONE,
    drag=Drag((0, 0, 1), 150),
    core=lambda: front(cores()["stub"], "stub"),
)
def stub():
    return front(stones()["stub"][0], "stub")


stub_back = model.copy(
    "stubBack", "Cột gãy sau", of="stub", rotation=BACK, drag=Drag((0, 0, 1), 150)
)


@model.part("skull", "Sọ trước", color=BONE, drag=Drag((0, 0, 1), 150))
def skull():
    return front(skull_local(), "skull")


skull_back = model.copy(
    "skullBack", "Sọ sau", of="skull", rotation=BACK, drag=Drag((0, 0, 1), 150)
)


@model.part(
    "chain",
    "Xích trước",
    color=IRON,
    drag=Drag((1, 0, 0), 80),
    print_rotation=CHAIN_PRINT,
    core=lambda: front_chain(chain_print_mesh()[1]),
)
def chain():
    return front_chain(chain_print_mesh()[0])


chain_back = model.copy(
    "chainBack", "Xích sau", of="chain", rotation=BACK, drag=Drag((-1, 0, 0), 80)
)


@model.part(
    "altar",
    "Bệ tay cầm trước",
    color=STONE,
    drag=Drag((-1, 0, 0), 100),
    core=lambda: front(cores()["altar"], "altar"),
)
def altar():
    return front(stones()["altar"][0], "altar")


altar_back = model.copy(
    "altarBack", "Bệ tay cầm sau", of="altar", rotation=BACK, drag=Drag((1, 0, 0), 100)
)


@model.part("fitCoupon", "Coupon thử khe", color=STONE, assembled=False)
def fit_coupon():
    """A slice of the plinth: one rib, both cradle walls and the air channel."""
    return stones()["plinth"][0] ^ art.box((-45, 10, 0), (45, 26, 70))


HALF = [c / 2 for c in CONSOLE]
DS4_TILT = (0, 90 - LEAN, 0)  # box frame: x = thickness (-n), y = width, z = depth (v)
DS4_HALF = (DS4[1] / 2, DS4[0] / 2, DS4[2] / 2)


def ds4_front(shape):
    return placed(shape, DS4_TILT, tuple(ds4_centre() + np.array(FRONT)))


model.reference(
    "console",
    "PS4 (tham khảo)",
    [Box("console", CONSOLE, (0, 0, CONSOLE_Z + CONSOLE[2] / 2), "#1b1b1f")],
    drag=Drag((0, 0, 1), 320),
)
model.reference(
    "ds4",
    "Tay cầm trước (tham khảo)",
    [
        Solid(
            "ds4", ds4_front(cq.Workplane("XY").box(DS4[1], DS4[0], DS4[2])), "#2a2a30"
        )
    ],
    drag=Drag(tuple(LEAN_V), 150),
)
model.reference(
    "ds4Back",
    "Tay cầm sau (tham khảo)",
    [
        Solid(
            "ds4Back",
            placed(
                ds4_front(cq.Workplane("XY").box(DS4[1], DS4[0], DS4[2])),
                BACK,
                (0, 0, 0),
            ),
            "#2a2a30",
        )
    ],
    drag=Drag((-LEAN_V[0], 0.0, LEAN_V[2]), 150),
)


def line(a, b, anchor_a, anchor_b, label, label_offset):
    return {
        "a": a,
        "b": b,
        "anchorA": anchor_a,
        "anchorB": anchor_b,
        "label": label,
        "labelOffset": label_offset,
    }


model.measure(
    "slot",
    "Khe đặt máy",
    kind="case",
    follow="plinth",
    color="#efb96e",
    label_width=70,
    lines=[
        line(
            [-27, -140, 66],
            [27, -140, 66],
            [-27, -117.5, 66],
            [27, -117.5, 66],
            "54 mm · Khe (máy 53)",
            [0, 0, 10],
        )
    ],
)
model.measure(
    "airGap",
    "Khe gió dưới máy",
    kind="case",
    follow="plinth",
    color="#efb96e",
    label_width=64,
    lines=[
        line(
            [-45, 0, 0],
            [-45, 0, 20],
            [-26.5, 0, 0],
            [-26.5, 0, 20],
            "20 mm · Gầm máy",
            [-30, 0, 0],
        )
    ],
)
model.measure(
    "footprint",
    "Đế 170 × 80",
    kind="case",
    follow="plinth",
    color="#efb96e",
    label_width=64,
    lines=[
        line(
            [-85, -145, 0],
            [85, -145, 0],
            [-85, -132.5, 0],
            [85, -132.5, 0],
            "170 mm · Đế rộng",
            [0, -10, 0],
        ),
        line(
            [100, -132.5, 0],
            [100, -52.5, 0],
            [85, -132.5, 0],
            [85, -52.5, 0],
            "80 mm · Đế sâu",
            [26, 0, 0],
        ),
    ],
)
model.measure(
    "pillar",
    "Cột cao",
    kind="case",
    follow="pillar",
    color="#efb96e",
    label_width=64,
    lines=[
        line(
            [60, -150, 0],
            [60, -150, 221.5],
            [60, -132.5, 0],
            [60, -109.5, 221.5],
            "221.5 mm · Đỉnh cột",
            [0, -6, 0],
        )
    ],
)
model.measure(
    "overall",
    "Cao tổng",
    kind="case",
    follow="plinth",
    color="#83caff",
    label_width=72,
    lines=[
        line(
            [-110, -92.5, 0],
            [-110, -92.5, 295],
            [-85, -92.5, 0],
            [-26.5, -92.5, 295],
            "295 mm · Cao cả máy",
            [-34, 0, 0],
        )
    ],
    variants={
        "console": [
            line(
                [-110, -92.5, 0],
                [-110, -92.5, 221.5],
                [-85, -92.5, 0],
                [43, -92.5, 221.5],
                "221.5 mm · Cao giá",
                [-34, 0, 0],
            )
        ]
    },
)
model.measure(
    "altar",
    "Bệ tay cầm",
    kind="case",
    follow="altar",
    color="#efb96e",
    label_width=64,
    lines=[
        line(
            [-180, -163.5, 0],
            [-86, -163.5, 0],
            [-180, -151.5, 0],
            [-86, -151.5, 0],
            "94 mm · Bệ rộng",
            [0, -10, 0],
        ),
        line(
            [-192, -151.5, 0],
            [-192, 30.5, 0],
            [-180, -151.5, 0],
            [-180, 30.5, 0],
            "182 mm · Bệ dài",
            [-26, 0, 0],
        ),
    ],
)
model.measure(
    "lean",
    "Góc nghiêng tay cầm",
    kind="component",
    follow="altar",
    visible_with="ds4",
    color="#83caff",
    label_width=56,
    lines=[
        line(
            [-118.0, -141.5, 10.2],
            [-90.638, -141.5, 85.375],
            [-78.0, -141.5, 10.2],
            [-90.638, -141.5, 85.375],
            "70° · Nghiêng",
            [0, -8, 14],
        )
    ],
)


def hold(value, start, rise, fall, end):
    rest = (0, 0, 0)
    return [
        (0, rest),
        (start, rest),
        (rise, value),
        (fall, value),
        (end, rest),
        (1, rest),
    ]


DS4_BACK_LIFT = (-LEAN_LIFT[0], 0.0, LEAN_LIFT[2])
FIRST, SECOND, THIRD, FOURTH = (
    (0.02, 0.14, 0.86, 0.98),
    (0.14, 0.24, 0.78, 0.88),
    (0.24, 0.36, 0.68, 0.8),
    (0.36, 0.48, 0.6, 0.7),
)
# Skulls, chains and controllers come off together, then the altars slide out, the console
# lifts and the pillars rise out of their sockets; reassembly runs in reverse.
model.animation(
    "assembly",
    "Tháo lắp",
    duration=14,
    open_pose={
        "skull": (0, 0, 90),
        "chain": (40, 0, 0),
        "ds4": LEAN_LIFT,
        "skullBack": (0, 0, 90),
        "chainBack": (-40, 0, 0),
        "ds4Back": DS4_BACK_LIFT,
        "altar": (-60, 0, 0),
        "altarBack": (60, 0, 0),
        "console": (0, 0, 220),
        "pillar": (0, 0, 60),
        "stub": (0, 0, 7),
        "pillarBack": (0, 0, 60),
        "stubBack": (0, 0, 7),
    },
    tracks={
        "skull": hold((0, 0, 90), *FIRST),
        "chain": hold((40, 0, 0), *FIRST),
        "ds4": hold(LEAN_LIFT, *FIRST),
        "skullBack": hold((0, 0, 90), *FIRST),
        "chainBack": hold((-40, 0, 0), *FIRST),
        "ds4Back": hold(DS4_BACK_LIFT, *FIRST),
        "altar": hold((-60, 0, 0), *SECOND),
        "altarBack": hold((60, 0, 0), *SECOND),
        "console": hold((0, 0, 220), *THIRD),
        "pillar": hold((0, 0, 60), *FOURTH),
        "stub": hold((0, 0, 7), *FOURTH),
        "pillarBack": hold((0, 0, 60), *FOURTH),
        "stubBack": hold((0, 0, 7), *FOURTH),
    },
    camera=[
        (0, (0, 0, 0)),
        (0.02, (0, 0, 0)),
        (0.3, (0, 0, 60)),
        (0.8, (0, 0, 60)),
        (0.98, (0, 0, 0)),
        (1, (0, 0, 0)),
    ],
    measure_reveal=(0.4, 0.6),
)


# ---------------------------------------------------------------- measurement helpers

PRINTED = {
    "plinth": plinth,
    "pillar": pillar,
    "stub": stub,
    "skull": skull,
    "chain": chain,
    "altar": altar,
    "fitCoupon": fit_coupon,
}
PRINT_ROTATION = {"chain": CHAIN_PRINT}


@cache
def print_meshes():
    """Each STL exactly as export writes it: part -> (bed translation, trimesh)."""
    return {
        name: print_frame(build(), PRINT_ROTATION.get(name, (0, 0, 0)))
        for name, build in PRINTED.items()
    }


def surface_top(mesh, points, z_min):
    """Highest upward-facing surface above each (x, y) point, ignoring faces below z_min."""
    tri = mesh.triangles[
        (mesh.face_normals[:, 2] > 1e-6) & (mesh.triangles_center[:, 2] > z_min)
    ]
    a, ab, ac = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    det = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    tops = []
    for x, y in points:
        px, py = x - a[:, 0], y - a[:, 1]
        u = (px * ac[:, 1] - py * ac[:, 0]) / det
        v = (ab[:, 0] * py - ab[:, 1] * px) / det
        inside = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        tops.append(
            (a[:, 2] + u * ab[:, 2] + v * ac[:, 2])[inside].max(initial=-np.inf)
        )
    return np.array(tops)


def printed_mass(mesh):
    """Rough slicer-style estimate: a SHELL_MM skin over the surface plus INFILL inside."""
    shell = min(mesh.volume, mesh.area * SHELL_MM)
    return (shell + INFILL * (mesh.volume - shell)) * PLA_G_MM3


def overhang_area(mesh):
    """Downward faces steeper than 45 deg from vertical, ignoring the bed face."""
    down = mesh.face_normals[:, 2] < -math.sqrt(0.5) - 1e-3
    off_bed = mesh.triangles_center[:, 2] > 0.05
    return round(float(mesh.area_faces[down & off_bed].sum()), 1)


def local_mesh(shape):
    verts, tris, _ = art.canonical_mesh(shape)
    return trimesh.Trimesh(verts, tris)


def centroid(shape):
    mesh = shape.to_mesh()
    return trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts).center_mass


@cache
def world():
    """Installed Manifold of every printed part in the assembly."""
    builds = {
        "plinth": plinth,
        "plinthBack": plinth_back,
        "pillar": pillar,
        "pillarBack": pillar_back,
        "stub": stub,
        "stubBack": stub_back,
        "skull": skull,
        "skullBack": skull_back,
        "chain": chain,
        "chainBack": chain_back,
        "altar": altar,
        "altarBack": altar_back,
    }
    return {part_id: build() for part_id, build in builds.items()}


@cache
def references():
    console = art.box(
        (-HALF[0], -HALF[1], CONSOLE_Z), (HALF[0], HALF[1], CONSOLE_Z + CONSOLE[2])
    )
    ds4 = ds4_front(art.box(tuple(-h for h in DS4_HALF), DS4_HALF))
    return {"console": console, "ds4": ds4, "ds4Back": placed(ds4, BACK, (0, 0, 0))}


def bodies():
    return {**world(), **references()}


@cache
def pair_overlaps():
    items = list(bodies().items())
    return {
        f"{a}~{b}": overlap(sa, sb)
        for i, (a, sa) in enumerate(items)
        for b, sb in items[i + 1 :]
    }


def no_overlap(pairs):
    bad = {pair: round(value, 4) for pair, value in pairs.items() if value >= EPS}
    if bad:
        raise CheckFailed(f"overlapping: {bad}")
    worst = max(pairs, key=pairs.get)
    return {
        "pairs_checked": len(pairs),
        "max_pair": worst,
        "max_volume_mm3": pairs[worst],
    }


def outside_nominal():
    """Final printable part minus its nominal core, mm³; simplify may move a surface by <= 0.05 mm."""
    return {
        name: (stones()[name][0] - art.to_manifold(cores()[name])).volume()
        for name in stones()
    }


# ---------------------------------------------------------------- checks
# Names match the reference implementation's verification.json.


@model.check("physical_fit_tested")
def physical_fit_tested():
    return {"tested": False, "note": "Not printed yet; print fitCoupon first"}


@model.check("all_parts_watertight_one_shell")
def watertight():
    report = {}
    for name, (_, mesh) in print_meshes().items():
        if not (
            mesh.is_watertight
            and mesh.is_winding_consistent
            and mesh.volume > 0
            and len(mesh.split()) == 1
        ):
            raise CheckFailed(f"{name} is not one watertight shell")
        report[name] = {
            "triangles": len(mesh.faces),
            "volume_mm3": round(float(mesh.volume), 1),
            "mass_g_solid": round(float(mesh.volume) * PLA_G_MM3, 1),
            "mass_g_estimate": round(printed_mass(mesh), 1),
            "overhang_mm2_over_45deg": overhang_area(mesh),
            "sha256": hashlib.sha256(mesh.export(file_type="stl")).hexdigest(),
        }
    return report


@model.check("fits_250_cube")
def fits_bed():
    sizes = {
        name: (mesh.bounds[1] - mesh.bounds[0]).round(3).tolist()
        for name, (_, mesh) in print_meshes().items()
    }
    too_big = [name for name, size in sizes.items() if max(size) > BED]
    if too_big:
        raise CheckFailed(f"larger than {BED} mm: {too_big}")
    return sizes


@model.check("under_60k_triangles")
def triangle_budget():
    counts = {name: len(mesh.faces) for name, (_, mesh) in print_meshes().items()}
    if max(counts.values()) > MAX_TRIS:
        raise CheckFailed(f"over {MAX_TRIS} triangles: {counts}")
    return counts


@model.check("no_part_intersects_console")
def console_clear():
    return no_overlap(
        {
            pair: value
            for pair, value in pair_overlaps().items()
            if "console" in pair.split("~")
        }
    )


@model.check("no_two_parts_overlap")
def parts_clear():
    return no_overlap(
        {
            pair: value
            for pair, value in pair_overlaps().items()
            if not set(pair.split("~")) & {"console", "ds4", "ds4Back"}
        }
    )


@model.check("ds4_envelope_intersects_no_part")
def ds4_clear():
    report = no_overlap(
        {
            pair: value
            for pair, value in pair_overlaps().items()
            if set(pair.split("~")) & {"ds4", "ds4Back"}
        }
    )
    # How far the controller can rise straight along its lean axis before touching anything.
    others = [body for part_id, body in bodies().items() if part_id != "ds4"]
    free_lift = 0
    for step in range(1, 151):
        moved = references()["ds4"].translate(tuple(step * LEAN_V))
        box = np.array(moved.bounding_box())
        near = [
            b
            for b in others
            if not (
                (box[:3] > np.array(b.bounding_box())[3:]).any()
                or (np.array(b.bounding_box())[:3] > box[3:]).any()
            )
        ]
        if any(overlap(moved, b) > EPS for b in near):
            break
        free_lift = step
    return {**report, "ds4_straight_lift_free_mm": free_lift}


def zone_clear(region):
    blocking = {
        part_id: round(overlap(shape, region), 4)
        for part_id, shape in bodies().items()
        if part_id != "console"
    }
    blocking = {part_id: value for part_id, value in blocking.items() if value >= EPS}
    if blocking:
        raise CheckFailed(f"blocked by {blocking}")
    return {"bodies_checked": len(bodies()) - 1}


@model.check("air_channel_clear")
def air_channel():
    ribs = m3.Manifold()
    for set_y in (-SET_Y, SET_Y):
        for rib_y in (-1, 1):
            center = set_y + rib_y * sum(RIB_Y) / 2
            ribs += art.box(
                (-30, center - 4, SLOT_FLOOR - 1), (30, center + 4, TOP + 1)
            )
    return zone_clear(
        art.box(
            (-HALF[0], -SET_Y - LOWER[1] / 2 - 1, SLOT_FLOOR),
            (HALF[0], SET_Y + LOWER[1] / 2 + 1, TOP),
        )
        - ribs
    )


@model.check("under_console_between_sets_clear")
def under_console():
    return zone_clear(
        art.box(
            (-HALF[0], -SET_Y + LOWER[1] / 2, 0), (HALF[0], SET_Y - LOWER[1] / 2, TOP)
        )
    )


@model.check("port_and_exhaust_zones_clear")
def ports():
    return zone_clear(
        art.box((-90, -HALF[1] - 60, 0), (90, -HALF[1], 300))
        + art.box((-90, HALF[1], 0), (90, HALF[1] + 60, 300))
    )


@model.check("tenon_clears_socket_by_0_15")
def tenon_clearance():
    """A tenon 0.15 mm bigger per side still fits the socket."""
    probe = art.box(
        (SOCKET_X - SHAFT / 2 - 0.15, -SET_Y - SHAFT / 2 - 0.15, FLOOR + 0.05),
        (SOCKET_X + SHAFT / 2 + 0.15, -SET_Y + SHAFT / 2 + 0.15, TOP),
    )
    value = overlap(plinth(), probe)
    if value >= EPS:
        raise CheckFailed(f"socket too tight: {value:.4f} mm³")
    return {
        "overlap_mm3": value,
        "socket": [SOCKET, SOCKET, SOCKET_DEPTH],
        "tenon": [SHAFT, SHAFT, TENON_H],
    }


@model.check("peg_clears_hole_by_0_15")
def peg_clearance():
    probe = front(
        art.to_manifold(cylinder_z(PEG_D + 0.3, STUB_H + 0.05, STUB_H + PEG_H + 0.5)),
        "stub",
    )
    value = overlap(skull(), probe)
    if value >= EPS:
        raise CheckFailed(f"peg hole too tight: {value:.4f} mm³")
    return {
        "overlap_mm3": value,
        "peg_diameter_height": [PEG_D, PEG_H],
        "hole_diameter_depth": [HOLE_D, HOLE_H],
    }


@model.check("chain_lifts_off_clear")
def chain_lift_off():
    """The chain slides 0–45 mm along +X off the hook without touching the pillar."""
    sweep = [
        overlap(chain().translate((step, 0, 0)), pillar()) for step in range(0, 46)
    ]
    if max(sweep) >= EPS:
        raise CheckFailed(f"chain removal blocked: {max(sweep):.4f} mm³")
    return {
        "max_overlap_mm3": max(sweep),
        "steps_mm": 45,
        "chain": {
            "links": LINKS,
            "wire": WIRE,
            "pitch": PITCH,
            "inner_width": 2 * LINK_R - WIRE,
            "hook_peg_diameter": HOOK_D,
            "break_gap": BREAK_GAP,
        },
    }


@model.check("tongue_clears_pocket_by_0_15")
def tongue_clearance():
    probe = art.box(
        (TONGUE[0][0] + 1, TONGUE[1][0] - 0.15 - SET_Y, TONGUE[2][0]),
        (TONGUE[0][1] + 0.15, TONGUE[1][1] + 0.15 - SET_Y, TONGUE[2][1] + 0.15),
    )
    value = overlap(plinth(), probe)
    if value >= EPS:
        raise CheckFailed(f"pocket too tight: {value:.4f} mm³")
    return {"overlap_mm3": value, "tongue_clearance": 0.2}


@model.check("altar_lip_faces_exact")
def altar_lip():
    """Lip height, thickness and gap from a section through the middle of the pocket.

    Flat faces have vertices only on their boundary, so the section is where the corners show up."""
    mesh = local_mesh(stones()["altar"][0])
    in_cheeks = (mesh.vertices[:, 1] < ALTAR_Y[0] + CHEEK_T - 1e-3) | (
        mesh.vertices[:, 1] > ALTAR_Y[1] - CHEEK_T + 1e-3
    )
    cheek_top = float(mesh.vertices[in_cheeks, 2].max())
    backrest_x = lean_point(BACKREST_REACH * DS4[2], -BACKREST_T)[0]
    section = mesh.section(
        plane_origin=(0, DS4_Y0 + DS4[0] / 2, 0), plane_normal=(0, 1, 0)
    )
    rel = section.vertices - np.array([ALTAR_EDGE[0], 0, ALTAR_EDGE[1]])
    lb, lc = rel @ LEAN_V, rel @ LEAN_N
    lip_in, lip_out = DS4[1] + LIP_GAP, DS4[1] + LIP_GAP + LIP_T
    near_lip = (lc > lip_in - 0.5) & (lc < lip_out + 0.5) & (lb > -0.5)
    side = (lb > -0.5) & (lb < LIP_H + 0.5) & (lc > lip_in - 0.5) & (lc < lip_out + 0.5)
    lip = {
        "top_b": float(lb[near_lip].max()),
        "inner_c": float(lc[side].min()),
        "outer_c": float(lc[side].max()),
    }
    if not (
        abs(lip["top_b"] - LIP_H) < 1e-3
        and abs(lip["inner_c"] - lip_in) < 1e-3
        and abs(lip["outer_c"] - lip_out) < 1e-3
    ):
        raise CheckFailed(f"lip faces moved: {lip}")
    if cheek_top > CHEEK_TOP + 1e-3 or backrest_x > -88:
        raise CheckFailed(
            f"altar outside its envelope: cheek top {cheek_top:.3f}, backrest x {backrest_x:.2f}"
        )
    return {
        "lean_deg": LEAN,
        "back_bottom_edge_xz": list(ALTAR_EDGE),
        "backrest_max_x": round(backrest_x, 2),
        "lip_outer_x": round(lean_point(0, lip_out)[0], 2),
        "cheek_top_max_z": round(cheek_top, 2),
        "ds4_envelope": list(DS4),
        "cheek_gap": CHEEK_GAP,
        "lip_gap": LIP_GAP,
        "backrest_reach_along_v": BACKREST_REACH * DS4[2],
        "lip_measured": {
            "height_mm": round(lip["top_b"], 4),
            "thickness_mm": round(lip["outer_c"] - lip["inner_c"], 4),
            "gap_to_envelope_mm": round(lip["inner_c"] - DS4[1], 4),
        },
    }


@model.check("erosion_step_inward_only")
def erosion_inward():
    """Displacement step alone, before simplify: only float32 rounding may stick out."""
    outward = {name: round(value, 4) for name, (_, value) in stones().items()}
    if max(outward.values()) >= 0.5:
        raise CheckFailed(f"erosion pushed material outward: {outward} mm³")
    return {
        "amplitude_mm": EROSION,
        "seeds": SEEDS,
        "refine_edge_mm": art.EROSION_EDGE,
        "simplify_tolerance_mm": art.SIMPLIFY_TOL,
        "volume_outside_blank_mm3": outward,
    }


@model.check("final_outside_nominal_below_0_5mm3")
def final_outside():
    outside = {name: round(value, 4) for name, value in outside_nominal().items()}
    if max(outside.values()) >= 0.5:
        raise CheckFailed(
            f"printable parts lie outside their nominal cores: {outside} mm³"
        )
    return outside


@model.check("sets_within_y_52_5_to_132_5")
def sets_within_y():
    """The stand sets stay in y = ±[52.5, 132.5]; altars and controllers reach further by design
    and are covered by the port and overlap checks instead."""
    spans = {}
    for part_id, shape in world().items():
        if part_id.startswith("altar"):
            continue
        box = shape.bounding_box()
        y_abs = sorted(abs(v) for v in (box[1], box[4]))
        if not (
            box[1] * box[4] > 0
            and y_abs[0] >= SET_Y - LOWER[1] / 2 - 1e-6
            and y_abs[1] <= SET_Y + LOWER[1] / 2 + 1e-6
        ):
            raise CheckFailed(f"{part_id} leaves its set: y {box[1]:.3f}..{box[4]:.3f}")
        spans[part_id] = [round(y_abs[0], 3), round(y_abs[1], 3)]
    corners = np.array([shape.bounding_box() for shape in bodies().values()])
    return {
        "abs_y_mm": spans,
        "assembly_bounds_mm": [
            corners[:, :3].min(axis=0).round(2).tolist(),
            corners[:, 3:].max(axis=0).round(2).tolist(),
        ],
    }


@model.check("stub_seat_flat")
def stub_seat():
    mesh = local_mesh(stones()["stub"][0])
    seat_faces = (mesh.face_normals[:, 2] > 0.9999) & (
        np.abs(mesh.triangles[:, :, 2] - STUB_H).max(axis=1) < 1e-4
    )
    seat_area = float(mesh.area_faces[seat_faces].sum())
    rim = mesh.vertices[np.linalg.norm(mesh.vertices[:, :2], axis=1) > PEG_D / 2 + 1, 2]
    if seat_area <= 0.6 * SHAFT**2:
        raise CheckFailed(f"stub seat too small: {seat_area:.0f} mm²")
    if rim.max() > STUB_H + 1e-3:
        raise CheckFailed("stub rim rises above the seat")
    return {
        "stub_seat_z": STUB_H,
        "stub_seat_flat_area_mm2": round(seat_area, 1),
        "stub_rim_max_z": round(float(rim.max()), 4),
    }


@model.check("broken_edges_within_limits")
def broken_edges():
    """Cradle walls keep their grip, the broken top stays in its zone, chips stay within depth."""
    _, chip_depths, top_lowest = tall_pillar_blank()
    plinth_mesh = local_mesh(stones()["plinth"][0])
    wall_grid = [
        (side * x, y)
        for side in (-1, 1)
        for x in np.arange(WALL_IN + 0.25, WALL_OUT - 1.2, 0.5)
        for y in np.arange(-WALL_Y + 1.25, WALL_Y - 1.2, 0.5)
    ]
    wall_tops = surface_top(plinth_mesh, wall_grid, z_min=TOP + 10)
    tall_top = float(stones()["pillar"][0].bounding_box()[5])
    if wall_tops.min() < WALL_MIN - EROSION - art.SIMPLIFY_TOL:
        raise CheckFailed(f"cradle wall broken too low: {wall_tops.min():.2f}")
    if (
        not TALL_H - BREAK_ZONE < tall_top <= TALL_H + 1e-3
        or top_lowest < TALL_H - BREAK_ZONE
    ):
        raise CheckFailed(f"broken top outside the top {BREAK_ZONE} mm")
    if not (5 <= len(chip_depths) <= 8 and max(chip_depths) <= CHIP_MAX):
        raise CheckFailed(f"corner chips out of range: {chip_depths}")
    return {
        "tall_pillar_top_z_local": round(tall_top, 2),
        "tall_pillar_top_z_world": round(tall_top + FLOOR, 2),
        "broken_top_lowest_z_local": round(top_lowest, 2),
        "corner_chips": len(chip_depths),
        "corner_chip_depths_mm": [round(d, 2) for d in chip_depths],
        "cradle_wall_top_z": [
            round(float(wall_tops.min()), 2),
            round(float(wall_tops.max()), 2),
        ],
    }


@model.check("contacts")
def contacts():
    """Each resting part touches what carries it: moved 0.5 mm down (chain 1 mm) it collides."""
    drop = (0, 0, -0.5)
    ds4 = references()["ds4"]
    measured = {
        "console_on_ribs": overlap(references()["console"].translate(drop), plinth()),
        "pillar_in_socket": overlap(pillar().translate(drop), plinth()),
        "stub_in_socket": overlap(stub().translate(drop), plinth()),
        "skull_on_stub": overlap(skull().translate(drop), stub()),
        "chain_on_hook": overlap(chain().translate((0, 0, -1.0)), pillar()),
        "ds4_on_seat": overlap(ds4.translate(tuple(-0.5 * LEAN_V)), altar()),
        "ds4_on_backrest": overlap(ds4.translate(tuple(-0.5 * LEAN_N)), altar()),
    }
    loose = [name for name, value in measured.items() if value <= EPS]
    if loose:
        raise CheckFailed(f"no contact: {loose}")
    rib_area = (
        overlap(
            plinth(),
            art.box((-HALF[0], -SET_Y - 50, TOP - 0.1), (HALF[0], -SET_Y + 50, TOP)),
        )
        / 0.1
    )
    return {
        "mm3_after_drop": {name: round(value, 3) for name, value in measured.items()},
        "rib_contact_area_mm2_per_set": round(rib_area, 1),
    }


@model.check("tipping_angle_at_least_20deg")
def tipping():
    """Combined centre of mass over the support polygon. Altars stand on their own bumpers and
    are not counted; the controllers are. Console-only is the worst case (stand mass -> 0)."""
    masses = [(CONSOLE_G, np.array([0, 0, CONSOLE_Z + CONSOLE[2] / 2]))]
    masses += [
        (shape.volume() * PLA_G_MM3, centroid(shape))
        for part_id, shape in world().items()
        if not part_id.startswith("altar")
    ]
    masses += [(DS4_G, centroid(references()[name])) for name in ("ds4", "ds4Back")]
    total = sum(m for m, _ in masses)
    com = sum(m * c for m, c in masses) / total
    report = {
        "pla_mass_g_solid": round(total - CONSOLE_G - 2 * DS4_G, 1),
        "controllers_g": 2 * DS4_G,
        "total_mass_g": round(total, 1),
        "center_of_mass": [round(float(v), 2) + 0.0 for v in com],
    }
    console_com = np.array([0, 0, CONSOLE_Z + CONSOLE[2] / 2])
    for mass_case, centre in (("", com), ("_console_only", console_com)):
        for label, (half_x, half_y) in {
            "bumper_centres": BUMPER_XY,
            "plinth_footprint": (LOWER[0] / 2, LOWER[1] / 2),
        }.items():
            x_edge, y_edge = half_x, SET_Y + half_y
            margins = [
                x_edge - centre[0],
                x_edge + centre[0],
                y_edge - centre[1],
                y_edge + centre[1],
            ]
            report[f"angle_deg_{label}{mass_case}"] = round(
                math.degrees(math.atan2(min(margins), centre[2])), 2
            )
    if (
        min(
            report["angle_deg_bumper_centres"],
            report["angle_deg_bumper_centres_console_only"],
        )
        < 20
    ):
        raise CheckFailed(f"tips over below 20°: {report}")
    return report


@model.check("ds4_centre_over_altar_bumpers")
def altar_alone():
    (bx0, bx1), (by0, by1) = ALTAR_BUMPERS
    ds4_c = ds4_centre()
    ds4_margin = min(ds4_c[0] - bx0, bx1 - ds4_c[0], ds4_c[1] - by0, by1 - ds4_c[1])
    if ds4_margin <= 0:
        raise CheckFailed("controller centre of mass outside the altar bumpers")
    shape = stones()["altar"][0]
    altar_g = shape.volume() * PLA_G_MM3
    pair_c = (altar_g * centroid(shape) + DS4_G * ds4_c) / (altar_g + DS4_G)
    pair_margin = min(
        pair_c[0] - bx0, bx1 - pair_c[0], pair_c[1] - by0, by1 - pair_c[1]
    )
    return {
        "ds4_centre_local": [round(float(v), 2) for v in ds4_c],
        "ds4_margin_to_bumper_polygon_mm": round(ds4_margin, 2),
        "altar_mass_g_solid": round(altar_g, 1),
        "altar_plus_ds4_tipping_deg": round(
            math.degrees(math.atan2(pair_margin, pair_c[2])), 2
        ),
    }


@model.check("step_ten_valid_solids")
def step_solids():
    """assembly.step holds the mechanical cores of both sets: plinth, pillar, stub, chain and altar.

    Export re-imports the written STEP and requires the same count of valid solids."""
    solids = {
        part.id: part.core() for part in model.parts if getattr(part, "core", None)
    }
    invalid = [
        part_id
        for part_id, shape in solids.items()
        if not shape.val().isValid() or len(shape.solids().vals()) != 1
    ]
    if len(solids) != 10 or invalid:
        raise CheckFailed(f"{len(solids)} cores, invalid: {invalid}")
    return {"solids": sorted(solids)}


@model.check("model_json_poses_match")
def poses_match():
    """Poses from printkit.pose, as export computes them, put each print mesh onto its CAD shape (bounds).

    This guards the model's rotations (the multi-axis chain, the back-set copies); printkit's
    own pose maths is covered by tests/test_export.py against the written model.json and STL."""
    poses, drift = {}, {}
    for name, (translation, _) in print_meshes().items():
        poses[name] = installed_pose(PRINT_ROTATION.get(name, (0, 0, 0)), translation)
    for part_id, shape in world().items():
        name = part_id.removesuffix("Back")
        pose = (
            poses[name]
            if part_id == name
            else composed_pose(BACK, (0, 0, 0), poses[name])
        )
        verts = print_meshes()[name][1].vertices @ euler_xyz_matrix(
            pose[1]
        ).T + np.array(pose[0])
        error = float(
            np.abs(
                np.concatenate([verts.min(axis=0), verts.max(axis=0)])
                - np.array(shape.bounding_box())
            ).max()
        )
        if error > 1e-3:
            drift[part_id] = round(error, 6)
    if drift:
        raise CheckFailed(f"viewer pose misplaces {drift}")
    return {"parts_checked": len(world()), "tolerance_mm": 1e-3}


def sample_track(keys, time):
    """Same easing as viewer/model-core.js sampleTrack."""
    if time <= keys[0]["time"]:
        return keys[0]["value"]
    for previous, following in zip(keys, keys[1:]):
        if time > following["time"]:
            continue
        t = (time - previous["time"]) / (following["time"] - previous["time"])
        eased = t * t * (3 - 2 * t)
        return [
            a + (b - a) * eased for a, b in zip(previous["value"], following["value"])
        ]
    return keys[-1]["value"]


def animation_samples(animation, step_mm=1.0):
    """Samples so no part moves more than step_mm between two of them; smoothstep peaks at 1.5x
    the mean speed of a keyframe interval."""
    rate = max(
        1.5 * math.dist(a["value"], b["value"]) / (b["time"] - a["time"])
        for track in animation["tracks"]
        for a, b in zip(track["keyframes"], track["keyframes"][1:])
    )
    return int(math.ceil(rate / step_mm)) + 1


@model.check("animation_collision_free")
def animation_clear():
    worst, total = (0.0, None, None), 0
    for animation in model.animations:
        samples = animation_samples(animation)
        total += samples
        for time in np.linspace(0, 1, samples):
            offsets = {
                track["part"]: tuple(sample_track(track["keyframes"], time))
                for track in animation["tracks"]
            }
            moved = {
                pid: body.translate(offsets.get(pid, (0, 0, 0)))
                for pid, body in bodies().items()
            }
            boxes = {pid: np.array(body.bounding_box()) for pid, body in moved.items()}
            ids = list(moved)
            for i, a in enumerate(ids):
                for b in ids[i + 1 :]:
                    if offsets.get(a, (0, 0, 0)) == offsets.get(b, (0, 0, 0)):
                        continue  # same rigid offset: covered by the installed-pose checks
                    if (boxes[a][:3] > boxes[b][3:]).any() or (
                        boxes[b][:3] > boxes[a][3:]
                    ).any():
                        continue
                    value = overlap(moved[a], moved[b])
                    if value > worst[0]:
                        worst = (value, f"{a}~{b}", f"{animation['id']} t={time:.4f}")
    if worst[0] >= EPS:
        raise CheckFailed(f"animation interpenetrates: {worst}")
    return {
        "max_overlap_mm3": worst[0],
        "pair": worst[1],
        "at": worst[2],
        "samples": total,
        "max_step_mm": 1.0,
    }
