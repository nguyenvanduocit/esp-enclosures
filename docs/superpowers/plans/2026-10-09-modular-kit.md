# Modular Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the V1 and V2 enclosure models with six kit modules (ESP32 mini, battery with charger, display, BME280, MPU6050, PIR), each one model in the web app, built on one shared standard.

**Architecture:** A new library `printkit/modules.py` holds the standard (20 mm units, flat 2 mm walls, a connector at the centre of every unit on every side, magnets on `+` faces and steel washers on `−` faces) and a `kit_model()` helper that registers parts, references, checks, measurements and the open-lid animation on a normal `printkit` `Model`. Each `models/kit-*/model.py` only declares its units, lid, cut-outs, internal posts and reference boards. Board envelopes live in `printkit/library/electronics.py`.

**Tech Stack:** Python 3.12, CadQuery 2.8.0, NumPy, pytest, `uv run`, the existing `printkit` CLI (`cad`, `slice`, `build`), Bambu Studio for slicing, headless Chrome for thumbnails.

**Spec:** `docs/superpowers/specs/2026-10-09-modular-kit-design.md`. A working geometry spike with the same formulas is in `docs/superpowers/explore/kit_spike.py` (read it for reference; it is deleted in Task 11).

## Global Constraints

- Millimetres, Z up. Module coordinates start at the outer corner `(0.1, 0.1, 0.1)`; registered models are shifted to be centred in X/Y and to sit on Z = 0.
- Constants: `GRID 20`, `CLEAR 0.1`, `EDGE_R 1.0`, `WALL 2.0`, `LID_PLAIN 1.8`, `LID_SKIRT 2.4`, `SKIRT_WALL 1.2`, `FIT 0.2`, `DISC_D 5.0`, `DISC_T 1.5`, `DISC_R 5.9`, `WASH_OD 12.0`, `WASH_ID 6.4`, `WASH_T 1.6`, `PORT_D 5.0`.
- `+x +y +z` faces carry 4 round magnets per unit; `-x -y -z` faces carry 1 steel washer per unit; every pocket is as deep as its part (parts end flush).
- Print parts must be one valid solid each; builds return `cq.Workplane` (`printkit/export.py:single_solid` calls `.val()` and `.solids()`).
- User-facing text (titles, README, print notes) is Vietnamese; identifiers, comments and check names are English.
- Run Python with `uv run`. Never push. Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- The ps4 stand model, `printkit` core, the viewer and `model.schema.json` are not modified.

## Review Focus

- A module whose lid face is declared plain gets a 1.8 mm lid and no lid fasteners (Task 2 test `test_plain_lid`).
- The smallest module, 1 × 1 × 1 with connectors on all six faces, keeps every pocket wall ≥ 0.8 mm and its exact outer size (Task 2 tests).
- A reference part that pokes into a wall or the lid skirt band must fail the model check (Task 3 test `test_reference_inside_wall_fails`).
- A cut-out that overlaps a connector pocket must fail the model check (Task 3 test `test_cut_into_pocket_fails`).
- Part ids such as `lidMagnets` must pass the viewer schema and the JS animation test, so `printkit cad` is run on every module (Tasks 4 to 9).

## File Structure

| File | Responsibility |
|---|---|
| `printkit/library/electronics.py` | Add `tp4056_usbc`, `bme280`, `mpu6050`, `hc_sr501`, `ili9341_24` reference envelopes (Task 1) |
| `printkit/modules.py` | The standard: constants, geometry, probes, `declare`, `kit_model` (Tasks 2, 3) |
| `tests/test_electronics.py`, `tests/test_modules.py` | Tests for the two libraries |
| `models/kit-esp32/`, `kit-battery/`, `kit-display/`, `kit-bme280/`, `kit-mpu6050/`, `kit-pir/` | One module each: `model.py`, `README.md`, `thumbnail.png`, generated files |
| `models.json`, `README.md`, `tests/test_catalog.py`, `tests/model-core.test.js` | Catalog and tests re-based on the kit (Task 10) |

---

### Task 1: Board envelopes

**Files:**
- Modify: `printkit/library/electronics.py` (append after `esp32_c3_supermini`)
- Test: `tests/test_electronics.py` (append)

**Interfaces:**
- Produces: `tp4056_usbc(at)`, `bme280(at)`, `mpu6050(at)`, `hc_sr501(at)`, `ili9341_24(at)`. Each takes `at=(x, y, z)` = centre of the PCB underside and returns a list of `Box`/`Solid` pieces (all have `.name`). Sizes come from shop listings and are illustrative.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_electronics.py`)

```python
import cadquery as cq

from printkit.library.electronics import bme280, hc_sr501, ili9341_24, mpu6050, tp4056_usbc


def top(pieces):
    return max(p.center[2] + p.size[2] / 2 for p in pieces if hasattr(p, 'size'))


def test_tp4056_usbc_envelope():
    pieces = tp4056_usbc(at=(36, 17.5, 16.75))
    by_name = {p.name: p for p in pieces}
    assert by_name['pcb'].size == (17, 28, 1.6)
    assert top(pieces) - 16.75 == approx(4.9)                      # listings: 4.1 to 4.9 mm tall
    assert by_name['usb'].center[2] == approx(16.75 + 1.6 + 1.65)  # USB-C axis 3.25 above the PCB underside
    assert by_name['usb'].center[1] - 3.75 == approx(17.5 - 14 - 0.8)  # port overhangs the -y edge by 0.8


def test_bme280_envelope():
    by_name = {p.name: p for p in bme280(at=(10, 9, 8.75))}
    assert by_name['pcb'].size == (15.4, 11.6, 1.6)
    assert by_name['header'].center[2] == approx(8.75 - 1.25)


def test_mpu6050_envelope():
    by_name = {p.name: p for p in mpu6050(at=(20, 20, 6))}
    assert by_name['pcb'].size == (20.5, 16, 1.6)
    assert by_name['header'].size == (20.32, 2.5, 2.5)


def test_hc_sr501_lens_is_a_solid_above_the_pcb():
    pieces = hc_sr501(at=(20, 20, 19.8))
    lens = next(p for p in pieces if p.name == 'lens')
    box = lens.shape.val().BoundingBox()
    assert (box.zmin, box.zmax) == approx((19.8 + 1.2, 19.8 + 1.2 + 18))
    assert box.xlen == approx(23)


def test_ili9341_envelope():
    by_name = {p.name: p for p in ili9341_24(at=(40, 25.55, 12.9))}
    assert by_name['pcb'].size == (70.5, 43.3, 1.6)
    assert by_name['glass'].center[2] + 1.6 == approx(12.9 + 1.6 + 3.2)  # glass top
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_electronics.py -q`
Expected: FAIL with `ImportError: cannot import name 'tp4056_usbc'`

- [ ] **Step 3: Implement** (append to `printkit/library/electronics.py`; also change its first import line to `import cadquery as cq` plus `from printkit.manifest import Box, Solid`)

```python
def tp4056_usbc(at=(0, 0, 0)):
    """TP4056 USB-C charger with protection, USB-C towards -y. Listings give 26 to 29 x 17 x 4.1 to 4.9 mm; this is 28 x 17 x 4.9."""
    x, y, z = at
    return [Box('pcb', (17, 28, 1.6), (x, y, z + 0.8), '#2b6fb3'),
            Box('usb', (9, 7.5, 3.3), (x, y - 11.05, z + 1.6 + 1.65), '#c3cbd0'),
            Box('ic', (5, 5, 1.5), (x, y + 4, z + 1.6 + 0.75), '#24343c')]


def bme280(at=(0, 0, 0)):
    """GY-BME280 breakout, 15.4 x 11.6 x 2.4 per listings; the 6-pin header body sits under the board along X."""
    x, y, z = at
    return [Box('pcb', (15.4, 11.6, 1.6), (x, y, z + 0.8), '#6a3fa0'),
            Box('chip', (2.5, 2.5, 0.9), (x + 2, y, z + 1.6 + 0.45), '#c3cbd0'),
            Box('header', (15.24, 2.5, 2.5), (x, y - 3.5, z - 1.25), '#27343c')]


def mpu6050(at=(0, 0, 0)):
    """GY-521 MPU6050, about 20.5 x 16 mm per listings; the 8-pin header body sits under the board along X."""
    x, y, z = at
    return [Box('pcb', (20.5, 16, 1.6), (x, y, z + 0.8), '#2b6fb3'),
            Box('chip', (4, 4, 0.9), (x, y, z + 1.6 + 0.45), '#24343c'),
            Box('header', (20.32, 2.5, 2.5), (x, y - 5, z - 1.25), '#27343c')]


def hc_sr501(at=(0, 0, 0)):
    """HC-SR501 PIR, 32 x 24 mm PCB and a dome lens of diameter 23 and height about 18 (listings disagree, 18 to 30 mm overall)."""
    x, y, z = at
    lens = cq.Workplane('XY').circle(11.5).extrude(18).translate((x, y, z + 1.2))
    return [Box('pcb', (32, 24, 1.2), (x, y, z + 0.6), '#2e8b57'),
            Solid('lens', lens, '#e8e2d0'),
            Box('header', (7.62, 2.5, 2.5), (x + 12, y - 9, z - 1.25), '#27343c')]


def ili9341_24(at=(0, 0, 0)):
    """2.4 inch ILI9341 module, 70.5 x 43.3 mm PCB (Waveshare listing) with the glass above it; the glass size is an assumption."""
    x, y, z = at
    return [Box('pcb', (70.5, 43.3, 1.6), (x, y, z + 0.8), '#2b6fb3'),
            Box('glass', (60, 40, 3.2), (x, y, z + 1.6 + 1.6), '#1c2a33')]
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_electronics.py -q`
Expected: PASS (the old `test_supermini_envelope` still passes)

- [ ] **Step 5: Commit**

```bash
git add printkit/library/electronics.py tests/test_electronics.py
git commit -m "Add TP4056, BME280, MPU6050, HC-SR501 and ILI9341 reference envelopes"
```

---

### Task 2: Kit standard geometry

**Files:**
- Create: `printkit/modules.py` (geometry half; Task 3 appends `declare` and `kit_model`)
- Test: `tests/test_modules.py`

**Interfaces:**
- Produces (all in `printkit/modules.py`):
  - constants listed in Global Constraints, `FACES`, `UP`, `DOWN` (face -> print rotation, Euler XYZ degrees), `EPS`
  - `ModuleSpec(cells, lid, plain=(), cuts=(), adds=())` frozen dataclass; `cuts` and `adds` hold `cq.Solid`s in module coordinates
  - `unit(face) -> np.ndarray`, `kind(face) -> 'magnet' | 'steel'`, `axes(face) -> (a, b)` unit vectors in the face plane, `disc_offsets(face) -> list[np.ndarray]`
  - `box(lo, hi)`, `cyl(base, direction, r, length)`, `ring(base, direction, od, idm, length)` -> `cq.Solid`; `vec(a) -> cq.Vector`; `wp(shape) -> cq.Workplane`
  - `bounds(spec) -> (lo, hi)`, `outer(cells) -> tuple[float]`, `connector_faces(spec)`, `lid_thickness(spec)`, `face_cells(spec, face)` yields `(cell, centre)`, `pockets(spec, face)` returns `[(centre, radius, depth, kind)]`, `cutters(spec, face)`, `cavity(spec)`, `shell_and_lid(spec) -> (shell, lid)` as `cq.Shape`
  - `Fastener` NamedTuple `(solid, kind, centre, face, cell)`, `fasteners(spec)`, `fastener_groups(spec) -> dict[str, cq.Compound]` (keys `magnets`, `washers`, `lidMagnets`, `lidWashers`, empty ones omitted), `bom(spec) -> {'magnets': int, 'washers': int}`
  - `pocket_problems(spec, shell, lid) -> int`, `plain_problems(spec, shell) -> int`, `cut_clash_volume(spec) -> float`, `pocket_walls(spec) -> (adjacent, same_face, to_port)` minimum distances in mm, `overlap_fraction(disc_centre, ring_centre) -> float`

- [ ] **Step 1: Write the failing tests** (`tests/test_modules.py`)

```python
import itertools

import numpy as np
import pytest
from pytest import approx

from printkit.modules import (DISC_R, DOWN, FACES, LID_PLAIN, UP, WALL, ModuleSpec, axes, bom, bounds, box, cut_clash_volume,
                              disc_offsets, fastener_groups, kind, lid_thickness, outer, overlap_fraction,
                              plain_problems, pocket_problems, pocket_walls, shell_and_lid, unit)
from printkit.pose import euler_xyz_matrix


def test_outer_size_is_units_times_grid_minus_clearance():
    assert outer((2, 4, 2)) == approx((39.8, 79.8, 39.8))


def test_positive_faces_carry_magnets_negative_faces_washers():
    assert [kind(f) for f in ('+x', '+y', '+z')] == ['magnet'] * 3
    assert [kind(f) for f in ('-x', '-y', '-z')] == ['steel'] * 3


@pytest.mark.parametrize('face', list(FACES))
def test_disc_ring_lies_in_the_face_plane_at_radius(face):
    offsets = disc_offsets(face)
    assert len(offsets) == 4
    for offset in offsets:
        assert np.linalg.norm(offset) == approx(DISC_R)
        assert offset @ unit(face) == approx(0)


@pytest.mark.parametrize('face', list(FACES))
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


SPEC = ModuleSpec(cells=(1, 1, 1), lid='+y')


@pytest.fixture(scope='module')
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
    assert bom(SPEC) == {'magnets': 12, 'washers': 3}
    assert set(fastener_groups(SPEC)) == {'magnets', 'washers', 'lidMagnets'}


def test_plain_lid():
    spec = ModuleSpec(cells=(1, 1, 1), lid='+y', plain=('+y',))
    assert lid_thickness(spec) == LID_PLAIN
    assert lid_thickness(SPEC) == WALL
    assert not any(name.startswith('lid') for name in fastener_groups(spec))
    assert bom(spec) == {'magnets': 8, 'washers': 3}


def test_plain_face_is_solid_and_cut_clash_is_zero():
    spec = ModuleSpec(cells=(2, 1, 1), lid='+y', plain=('-y',), cuts=(box((10, 0, 8), (20, 3, 12)),))
    shell, _ = shell_and_lid(spec)
    assert plain_problems(spec, shell) == 0
    assert cut_clash_volume(spec) == approx(0, abs=1e-6)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_modules.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'printkit.modules'`

- [ ] **Step 3: Implement** (`printkit/modules.py`)

```python
"""Kit standard: modules of 20 mm units with flat 2 mm walls and a connector at the centre of every unit on every side.

A connector is a wire port with parts glued flush in pockets drilled from outside: + faces carry 4 round magnets,
- faces one carbon-steel washer. A joint is always magnet to steel and holds at any turn about its axis.
Module coordinates start at the outer corner (CLEAR, CLEAR, CLEAR); `declare` shifts the registered model so the module
is centred in X/Y and sits on Z = 0."""
import itertools
from dataclasses import dataclass
from typing import NamedTuple

import cadquery as cq
import numpy as np

GRID, CLEAR, EDGE_R, WALL = 20.0, 0.1, 1.0, 2.0
LID_PLAIN, LID_SKIRT, SKIRT_WALL, FIT = 1.8, 2.4, 1.2, 0.2
DISC_D, DISC_T, DISC_R = 5.0, 1.5, 5.9
DISC_POCKET = DISC_D + 0.1
WASH_OD, WASH_ID, WASH_T = 12.0, 6.4, 1.6
WASH_POCKET = WASH_OD + 0.1
PORT_D = 5.0
EPS = 0.02

FACES = {'+x': (0, 1), '-x': (0, -1), '+y': (1, 1), '-y': (1, -1), '+z': (2, 1), '-z': (2, -1)}
# Euler XYZ degrees: UP turns the named face to +Z (shell, opening up), DOWN to -Z (lid, outer face on the bed)
UP = {'+z': (0, 0, 0), '-z': (180, 0, 0), '+x': (0, -90, 0), '-x': (0, 90, 0), '+y': (90, 0, 0), '-y': (-90, 0, 0)}
DOWN = {'+z': (180, 0, 0), '-z': (0, 0, 0), '+x': (0, 90, 0), '-x': (0, -90, 0), '+y': (-90, 0, 0), '-y': (90, 0, 0)}


@dataclass(frozen=True)
class ModuleSpec:
    cells: tuple          # units along x, y, z
    lid: str              # the face the lid closes, e.g. '+y'
    plain: tuple = ()     # faces without connectors
    cuts: tuple = ()      # cq.Solids cut out of the shell (USB slot, window, vents), module coordinates
    adds: tuple = ()      # cq.Solids fused to the shell (posts, ribs), module coordinates


def vec(a):
    return cq.Vector(*[float(x) for x in a])


def wp(shape):
    return shape if isinstance(shape, cq.Workplane) else cq.Workplane('XY').add(shape)


def unit(face):
    axis, sign = FACES[face]
    v = np.zeros(3)
    v[axis] = sign
    return v


def kind(face):
    return 'magnet' if FACES[face][1] > 0 else 'steel'


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
    return cyl(base, direction, od / 2, length).cut(cyl(base, direction, idm / 2, length))


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
        if kind(face) == 'magnet':
            out += [(c + o, DISC_POCKET / 2, DISC_T, 'magnet') for o in disc_offsets(face)]
        else:
            out.append((c, WASH_POCKET / 2, WASH_T, 'steel'))
    return out


def cutters(spec, face):
    n = unit(face)
    out = [cyl(p + n * EPS, -n, r, d + EPS) for p, r, d, _ in pockets(spec, face)]
    thick = lid_thickness(spec) if face == spec.lid else WALL
    out += [cyl(c + n * EPS, -n, PORT_D / 2, thick + 2 * EPS) for _, c in face_cells(spec, face)]
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


def shell_and_lid(spec):
    lo, hi = bounds(spec)
    axis, sign = FACES[spec.lid]
    t = lid_thickness(spec)
    body = cq.Workplane('XY').box(*(hi - lo), centered=False).edges().fillet(EDGE_R).val().translate(vec(lo))
    slab_lo, slab_hi = lo - 1, hi + 1
    if sign > 0:
        slab_lo[axis] = hi[axis] - t
    else:
        slab_hi[axis] = lo[axis] + t
    slab = box(slab_lo, slab_hi)
    cav_lo, cav_hi = cavity(spec)
    shell = body.cut(slab).cut(box(cav_lo, cav_hi))
    plate = body.intersect(slab)
    shell_cutters = [c for face in connector_faces(spec) if face != spec.lid for c in cutters(spec, face)]
    if spec.adds:
        shell = shell.fuse(*spec.adds)
    shell = shell.cut(*shell_cutters, *spec.cuts).clean()
    if spec.lid in connector_faces(spec):
        plate = plate.cut(*cutters(spec, spec.lid))
    s_lo, s_hi = cav_lo + FIT, cav_hi - FIT          # skirt inset FIT from every wall
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
            if kind(face) == 'magnet':
                for o in disc_offsets(face):
                    out.append(Fastener(cyl(c + o - n * DISC_T, n, DISC_D / 2, DISC_T), 'magnet', c + o, face, cell))
            else:
                out.append(Fastener(ring(c - n * WASH_T, n, WASH_OD, WASH_ID, WASH_T), 'steel', c, face, cell))
    return out


def fastener_groups(spec):
    """{'magnets', 'washers', 'lidMagnets', 'lidWashers'} -> cq.Compound, empty groups left out."""
    lists = {}
    for f in fasteners(spec):
        name = ('lid' if f.face == spec.lid else '') + ('Magnets' if f.kind == 'magnet' else 'Washers')
        lists.setdefault(name[0].lower() + name[1:], []).append(f.solid)
    return {name: cq.Compound.makeCompound(solids) for name, solids in lists.items()}


def bom(spec):
    items = fasteners(spec)
    return {'magnets': sum(f.kind == 'magnet' for f in items), 'washers': sum(f.kind == 'steel' for f in items)}


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
                wrong += shell.isInside(back, 1e-4) and not any(post.isInside(back, 1e-4) for post in spec.adds)
        for _, c in face_cells(spec, face):
            wrong += body.isInside(vec(c - n * 0.2), 1e-4) or body.isInside(vec(c - n * (thick - 0.2)), 1e-4)
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
    return sum(cut.intersect(c).Volume() for cut in spec.cuts for face in connector_faces(spec) for c in cutters(spec, face))


def pocket_walls(spec):
    """Smallest wall in mm between pockets of adjacent faces, between pockets of one face, and from a magnet pocket to the port.

    Measured on one unit with a connector on every side, because the spec's `cells` do not change these distances."""
    unit_spec = ModuleSpec(cells=(1, 1, 1), lid=spec.lid)
    cyls = []
    for face in FACES:
        n = unit(face)
        cyls += [(face, cyl(p, -n, r, d)) for p, r, d, _ in pockets(unit_spec, face)]
    pairs = list(itertools.combinations(cyls, 2))
    adjacent = min(a[1].distance(b[1]) for a, b in pairs if abs(unit(a[0]) @ unit(b[0])) < 0.5)
    same_face = min(a[1].distance(b[1]) for a, b in pairs if a[0] == b[0])
    to_port = min(cyl(c, -unit(f), PORT_D / 2, WALL).distance(cyl(p, -unit(f), r, d))
                  for f in FACES for _, c in face_cells(unit_spec, f)
                  for p, r, d, k in pockets(unit_spec, f) if k == 'magnet')
    return adjacent, same_face, to_port


def overlap_fraction(disc_centre, ring_centre):
    """Share of a magnet's face that lies over the washer annulus; both lie in one plane (2D points)."""
    grid = np.linspace(-DISC_D / 2, DISC_D / 2, 81)
    hit = total = 0
    for x, y in itertools.product(grid, grid):
        if x * x + y * y <= (DISC_D / 2) ** 2:
            total += 1
            r = np.hypot(disc_centre[0] + x - ring_centre[0], disc_centre[1] + y - ring_centre[1])
            hit += WASH_ID / 2 <= r <= WASH_OD / 2
    return hit / total
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_modules.py -q`
Expected: PASS (about 10 to 30 seconds; the CAD tests dominate)

- [ ] **Step 5: Commit**

```bash
git add printkit/modules.py tests/test_modules.py
git commit -m "Add the kit standard geometry: units, connectors, shell, lid, fasteners and probes"
```

---

### Task 3: `declare` and `kit_model`

**Files:**
- Modify: `printkit/modules.py` (append)
- Test: `tests/test_modules.py` (append)

**Interfaces:**
- Consumes: everything from Task 2; `printkit.manifest` (`Box`, `Drag`, `Model`, `Print`, `Solid`, `dim`, `pulse`); `printkit.checks.CheckFailed`, `clear`; `printkit.shapes.box_solid`.
- Produces: `kit_model(model_id, *, title, description, spec, color, refs=(), notes=(), sections=()) -> Model`. `refs` is a list of `(id, label, pieces)` where `pieces` are `Box`/`Solid` in module coordinates. The model has parts `shell`, `lid`, references `magnets`/`washers`/`lidMagnets`/`lidWashers` (when non-empty) and each `refs` entry, one measurement `case`, the animation `open`, and these checks (names exact): `Outer size equals units x 20 - 0.2 mm`, `Lid clears shell`, `Magnets and washers sit in their pockets`, `Connectors: pockets void, floors solid, interior flat, ports open`, `Plain faces are solid wall`, `Cut-outs clear every pocket`, `Reference parts clear shell and lid`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_modules.py`)

```python
from printkit.export import ModelError, built as build_part, run_checks
from printkit.manifest import Box, PrintPart
from printkit.modules import kit_model


def small_model(**changes):
    options = dict(title='T', description='d', spec=SPEC, color='#367c85')
    options.update(changes)
    return kit_model('kit-test', **options)


def test_kit_model_registers_parts_references_and_checks():
    model = small_model()
    ids = [part.id for part in model.parts]
    assert ids == ['shell', 'lid', 'magnets', 'washers', 'lidMagnets']
    assert [name for name, _ in model.checks][:3] == ['Outer size equals units x 20 - 0.2 mm', 'Lid clears shell',
                                                        'Magnets and washers sit in their pockets']
    assert [a['id'] for a in model.animations] == ['open']
    assert model.info['dimensions'] == approx([19.8, 19.8, 19.8])


def test_kit_model_builds_single_solids_and_passes_its_checks():
    model = small_model()
    for part in model.parts:
        if isinstance(part, PrintPart):
            build_part(part.id, part.build)
    results = run_checks(model)
    assert results['Outer size equals units x 20 - 0.2 mm']['outer_mm'] == approx([19.8, 19.8, 19.8])


def test_reference_inside_wall_fails():
    bad = [('big', 'Big', [Box('b', (30, 30, 30), (10, 10, 10), '#fff')])]
    with pytest.raises(ModelError, match='Reference parts clear shell and lid'):
        run_checks(small_model(refs=bad))


def test_cut_into_pocket_fails():
    spec = ModuleSpec(cells=(1, 1, 1), lid='+y', cuts=(box((8, 0, 8), (12, 3, 12)),))
    with pytest.raises(ModelError, match='Cut-outs clear every pocket'):
        run_checks(small_model(spec=spec))
```
(`box` is already in the import list from Task 2.)

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_modules.py -q -k "kit_model or reference_inside or cut_into"`
Expected: FAIL with `ImportError: cannot import name 'kit_model'`

- [ ] **Step 3: Implement** (append to `printkit/modules.py`; add these imports at the top of the file: `from functools import cache`, `import math`, `from printkit.checks import CheckFailed, clear`, `from printkit.manifest import Box, Drag, Model, Print, Solid, dim, pulse`, `from printkit.shapes import box_solid`)

```python
MAGNET_COLOR, WASHER_COLOR, LID_COLOR = '#ef5b5b', '#c9d3d9', '#d9d2b8'
GROUP_LABELS = {'magnets': ('Nam châm 5×1.5', MAGNET_COLOR), 'washers': ('Vòng đệm M6', WASHER_COLOR),
                'lidMagnets': ('Nam châm ở nắp', MAGNET_COLOR), 'lidWashers': ('Vòng đệm ở nắp', WASHER_COLOR)}
STANDARD_NOTES = [
    'Mặt dương (+x, +y, +z) lắp 4 nam châm tròn 5×1,5 mỗi đơn vị. Mặt âm (−x, −y, −z) lắp 1 vòng đệm thép M6 (12×6,4×1,6) mỗi đơn vị. Mối ghép luôn là nam châm hút sắt.',
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
        for ref_id, _, pieces in refs:
            for piece in pieces:
                clear(reference_solid(piece), shell=shell, lid=lid)


def kit_model(model_id, *, title, description, spec, color, refs=(), notes=(), sections=()):
    W, L, H = outer(spec.cells)
    size = max(W, L, H)
    grid = int(20 * math.ceil(3 * size / 20))
    info = {'summary': 'Chưa in thử', 'sections': [
        {'title': 'Lắp nam châm và vòng đệm', 'rows': [], 'notes': [*STANDARD_NOTES, *notes], 'links': []}, *sections]}
    model = Model(model_id, title=title, description=description, category='Module', status='Chưa in thử',
                  thumbnail='thumbnail.png', dimensions=(W, L, H),
                  camera={'position': [1.2 * size, -2.0 * size, 1.4 * size], 'target': [0, 0, H / 2],
                          'minDistance': 0.6 * size, 'maxDistance': 6 * size},
                  grid={'size': grid, 'divisions': grid // 10}, print_info=info,
                  print=Print(layer=0.16, first_layer=0.2, walls=3, infill=(15, 'gyroid'), supports=False, brim='auto',
                              extra={'top_shell_layers': 5, 'bottom_shell_layers': 5, 'wall_generator': 'arachne'}))
    declare(model, spec, color=color, refs=refs)
    return model
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_modules.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add printkit/modules.py tests/test_modules.py
git commit -m "Add declare and kit_model: parts, references, checks, measurements and the open-lid animation"
```

---

### Task 4: `kit-esp32` (Module ESP32-C3 mini)

**Files:**
- Create: `models/kit-esp32/model.py`, `models/kit-esp32/README.md`, `models/kit-esp32/thumbnail.png` (placeholder now, real one in Task 11)
- Generated by `cad`: `shell.stl`, `lid.stl`, `assembly.step`, `model.json`, `verification.json`, `reference/*.stl`

**Interfaces:**
- Consumes: `printkit.modules` (`ModuleSpec`, `box`, `cyl`, `kit_model`, `bounds`, `WALL`), `printkit.library.electronics.esp32_c3_supermini`.
- Produces: `model` (module-level), id `kit-esp32`.

- [ ] **Step 1: Write the model** (`models/kit-esp32/model.py`)

```python
"""Module ESP32-C3 mini: 2 x 2 x 2 units. ESP32-C3 SuperMini on four posts, USB-C at mid height. Millimetres, Z up."""
import itertools

from printkit.library.electronics import esp32_c3_supermini
from printkit.modules import WALL, ModuleSpec, bounds, box, cyl, kit_model

CELLS = (2, 2, 2)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX = (LO[0] + HI[0]) / 2
FLOOR = LO[2] + WALL
BOARD_Z = (LO[2] + HI[2]) / 2 - 3.2                  # USB-C axis at mid height, in the channel between the two connector rows
BOARD_Y = LO[1] + WALL + 0.5 + 12.75                 # PCB front 0.5 mm from the -y wall, USB overhang 1.5 mm
USB_SLOT = box((CX - 6, 0, BOARD_Z + 0.2), (CX + 6, LO[1] + WALL + 1, BOARD_Z + 6.2))
POSTS = tuple(cyl((CX + sx, BOARD_Y + sy, FLOOR - 0.5), (0, 0, 1), 1.5, BOARD_Z - FLOOR + 0.5)
              for sx, sy in itertools.product((-4.6, 4.6), (-7.4, 7.4)))

model = kit_model(
    'kit-esp32', title='Module ESP32-C3 mini',
    description='Bo ESP32-C3 SuperMini trong khối 2×2×2, cổng USB-C ở mặt trước.',
    spec=ModuleSpec(cells=CELLS, lid='+y', cuts=(USB_SLOT,), adds=POSTS), color='#367c85',
    refs=[('board', 'ESP32-C3 SuperMini', esp32_c3_supermini(at=(CX, BOARD_Y, BOARD_Z)))],
    notes=['Bốn trụ đỡ mặt dưới PCB; bo cần cố định thêm bằng keo hoặc băng dính.',
           'Khe USB-C nằm trong dải giữa hai hàng lỗ khoét ở mặt −y, nên không cắt vào lỗ nào.'])
```

- [ ] **Step 2: Create the placeholder thumbnail and build**

```bash
uv run python -c "from printkit.cli import placeholder_png; open('models/kit-esp32/thumbnail.png','wb').write(placeholder_png())"
uv run printkit cad kit-esp32
```
Expected: `kit-esp32: 2 print parts, 7 checks passed`. If a check fails, read its message and fix `model.py` (do not loosen the library). Warnings about print orientation are printed to stderr and are acceptable; copy them into the README. If a clearance check reports an overlap below 0.01 mm³ where a post meets the underside of a board, shorten that post by 0.05 mm.

- [ ] **Step 3: Write the README** (`models/kit-esp32/README.md`, Vietnamese). Use this outline for every module README:

```markdown
# Module ESP32-C3 mini

Mở trong [app chung](../../#model/kit-esp32). Khối 2×2×2 đơn vị (39,8 × 39,8 × 39,8 mm), nắp ở mặt +y.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
| ESP32-C3 SuperMini | 1 | 18 × 22,5 mm, chân hàn xuống |
| Nam châm tròn 5×1,5 | 4 mỗi mối ghép (lắp kín: <bom magnets>) | Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 1 mỗi mối ghép (lắp kín: <bom washers>) | Không dùng inox |

## Giả định
- Kích thước bo từ trang bán hàng; đo bo của bạn trước khi in.
- (các giả định riêng của module)

## Lắp
- Thứ tự dán, hướng mặt, đặt bo lên trụ, luồn dây qua cổng Ø5.

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
```
Fill `<bom ...>` from `uv run python -c "from printkit.modules import bom; ..."` using the module's `spec`.

- [ ] **Step 4: Verify the generated output is complete**

Run: `ls models/kit-esp32 && uv run python -c "import json; m=json.load(open('models/kit-esp32/model.json')); print([p['id'] for p in m['parts']], m['dimensions'])"`
Expected: `['shell', 'lid', 'magnets', 'washers', 'lidMagnets', 'board'] [39.8, 39.8, 39.8]`

- [ ] **Step 5: Commit**

```bash
git add models/kit-esp32
git commit -m "Add kit-esp32: ESP32-C3 mini module"
```

---

### Task 5: `kit-battery` (Module pin 18650 + sạc)

**Files:**
- Create: `models/kit-battery/model.py`, `README.md`, `thumbnail.png` (placeholder)

**Interfaces:**
- Consumes: as Task 4, plus `printkit.library.electronics.tp4056_usbc`, `printkit.manifest.Box, Solid`, `cadquery`.
- Produces: `model`, id `kit-battery`.

- [ ] **Step 1: Write the model**

```python
"""Module pin 18650 + sạc: 3 x 4 x 2 units. 18650 holder against -x, TP4056 USB-C charger on four posts beside it. Millimetres, Z up."""
import itertools

import cadquery as cq

from printkit import Box, Solid
from printkit.library.electronics import tp4056_usbc
from printkit.modules import WALL, ModuleSpec, bounds, box, cyl, kit_model

CELLS = (3, 4, 2)
LO, HI = bounds(ModuleSpec(CELLS, '+x'))
FLOOR = LO[2] + WALL
HOLDER = (22, 75, 18)                                 # open single 18650 holder, 75 x 22 x 18 per listings
HOLDER_X = LO[0] + WALL + 0.8 + HOLDER[0] / 2          # 0.8 mm against the -x wall for adhesive
HOLDER_Z = FLOOR + 0.8
CELL_Z = HOLDER_Z + 10.3
CY = (LO[1] + HI[1]) / 2
CHARGER = (36.0, 17.5, 16.75)                          # PCB underside centre; the USB-C axis ends at z = 20, mid height
CHARGER_POSTS = tuple(cyl((CHARGER[0] + sx, CHARGER[1] + sy, FLOOR - 0.5), (0, 0, 1), 1.5, CHARGER[2] - FLOOR + 0.5)
                      for sx, sy in itertools.product((-6, 6), (-10, 10)))
USB_SLOT = box((CHARGER[0] - 5.2, 0, 17.7), (CHARGER[0] + 5.2, LO[1] + WALL + 1, 22.3))

cell = cq.Workplane('XY').add(cq.Solid.makeCylinder(9.25, 65.3, cq.Vector(HOLDER_X, CY - 32.65, CELL_Z), cq.Vector(0, 1, 0)))

model = kit_model(
    'kit-battery', title='Module pin 18650 + sạc',
    description='Một viên 18650 trong khay hở cùng mạch sạc TP4056 USB-C, khối 3×4×2.',
    spec=ModuleSpec(cells=CELLS, lid='+x', cuts=(USB_SLOT,), adds=CHARGER_POSTS), color='#5f8f5b',
    refs=[('holder', 'Khay pin 18650', [Box('holder', HOLDER, (HOLDER_X, CY, HOLDER_Z + HOLDER[2] / 2), '#303d46')]),
          ('cell', 'Pin 18650', [Solid('cell', cell, '#87b483')]),
          ('charger', 'Mạch sạc TP4056 USB-C', tp4056_usbc(at=CHARGER))],
    notes=['Khoảng trống trong chiều dài là 75,8 mm cho khay 75 mm: chỉ còn 0,4 mm, hãy đo khay thật.',
           'Mạch sạc đặt trên bốn trụ; cổng USB-C nhìn ra khe ở mặt −y, nằm giữa hai hàng lỗ khoét.',
           'Không có mạch tăng áp; bạn tự chọn cách nối pin với ESP32-C3 SuperMini.',
           'Thay pin bằng cách mở nắp ở mặt +x.'])
```

- [ ] **Step 2: Build and fix**

```bash
uv run python -c "from printkit.cli import placeholder_png; open('models/kit-battery/thumbnail.png','wb').write(placeholder_png())"
uv run printkit cad kit-battery
```
Expected: `kit-battery: 2 print parts, 7 checks passed`. Reference-part clearance is the likely failure; adjust the holder or charger position, never the library.

- [ ] **Step 3: README** following Task 4's outline. "Cần mua": 18650 holder (1), TP4056 USB-C charger with protection (1), 18650 cell (1), magnets and washers with `bom(spec)` counts. Assumptions: A2 of the spec; charger sizes 26 to 29 × 17 × 4.1 to 4.9 from listings.

- [ ] **Step 4: Verify** `ls models/kit-battery` shows `shell.stl lid.stl model.json assembly.step verification.json reference`.

- [ ] **Step 5: Commit**

```bash
git add models/kit-battery
git commit -m "Add kit-battery: 18650 and TP4056 charger module"
```

---

### Task 6: `kit-display` (Module màn hình 2.4")

**Files:** Create `models/kit-display/model.py`, `README.md`, `thumbnail.png` (placeholder).

**Interfaces:** consumes `printkit.library.electronics.ili9341_24`; produces id `kit-display`.

- [ ] **Step 1: Write the model**

```python
"""Module màn hình 2.4": 4 x 3 x 1 units. ILI9341 board under a 49 x 37 window in the +z face. Millimetres, Z up."""
from printkit.library.electronics import ili9341_24
from printkit.modules import WALL, ModuleSpec, bounds, box, kit_model

CELLS = (4, 3, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX = (LO[0] + HI[0]) / 2
PY = LO[1] + WALL + 0.8 + 43.3 / 2                    # PCB 0.8 mm from the -y wall
GLASS_TOP = HI[2] - WALL - 0.2                        # glass sits 0.2 mm under the plain top wall
PCB_Z = GLASS_TOP - 3.2 - 1.6                         # PCB underside
WINDOW = box((CX - 24.48, PY - 18.36, HI[2] - WALL - 1), (CX + 24.48, PY + 18.36, HI[2] + 1))   # active area 48.96 x 36.72

model = kit_model(
    'kit-display', title='Module màn hình 2.4"',
    description='Màn hình TFT 2.4" ILI9341 dưới khung hiển thị 49×37 mm, khối 4×3×1.',
    spec=ModuleSpec(cells=CELLS, lid='+y', plain=('+z',), cuts=(WINDOW,)), color='#7b6cd9',
    refs=[('display', 'Màn hình ILI9341 2.4"', ili9341_24(at=(CX, PY, PCB_Z)))],
    notes=['Mặt +z là màn hình nên không có điểm nối.',
           'Cửa sổ 49×37 mm theo vùng hiển thị 48,96×36,72 mm; kính 60×40 mm là giả định, hãy đo màn hình của bạn.',
           'Bo lắp từ phía nắp +y rồi trượt vào dưới khung.'])
```

- [ ] **Step 2: Build and fix**

```bash
uv run python -c "from printkit.cli import placeholder_png; open('models/kit-display/thumbnail.png','wb').write(placeholder_png())"
uv run printkit cad kit-display
```
Expected: `kit-display: 2 print parts, 7 checks passed`.

- [ ] **Step 3: README** (Task 4 outline). Assumption A1; the board is 70.5 × 43.3 mm; interior along x is 75.8 mm and the board 70.9 with slack.

- [ ] **Step 4: Verify** `uv run python -c "import json; print(json.load(open('models/kit-display/model.json'))['dimensions'])"` prints `[79.8, 59.8, 19.8]`.

- [ ] **Step 5: Commit**

```bash
git add models/kit-display
git commit -m "Add kit-display: 2.4 inch ILI9341 module"
```

---

### Task 7: `kit-bme280` (Module cảm biến BME280)

**Files:** Create `models/kit-bme280/model.py`, `README.md`, `thumbnail.png` (placeholder).

**Interfaces:** consumes `printkit.library.electronics.bme280`; produces id `kit-bme280`.

- [ ] **Step 1: Write the model**

```python
"""Module cảm biến BME280: 1 x 1 x 1 unit. GY-BME280 board on two ribs; the -y face is plain with vent slots. Millimetres, Z up."""
from printkit.library.electronics import bme280
from printkit.modules import WALL, ModuleSpec, bounds, box, cyl, kit_model

CELLS = (1, 1, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX, CZ = (LO[0] + HI[0]) / 2, (LO[2] + HI[2]) / 2
BOARD = (CX, 9.1, CZ - 1.2)                            # PCB underside centre; PCB spans y 3.3 to 14.9, below the lid skirt band (y >= 15.5)
VENTS = tuple(box((CX + dx - 0.8, 0, CZ - 4.5), (CX + dx + 0.8, LO[1] + WALL + 0.5, CZ + 4.5)) for dx in (-4, 0, 4))
RIBS = tuple(cyl((CX + dx, 11.5, LO[2] + WALL - 0.5), (0, 0, 1), 1.2, BOARD[2] - (LO[2] + WALL) + 0.5) for dx in (-5.5, 5.5))

model = kit_model(
    'kit-bme280', title='Module cảm biến BME280',
    description='Cảm biến nhiệt độ, độ ẩm, áp suất GY-BME280 trong khối 1×1×1, mặt trước có khe thoáng.',
    spec=ModuleSpec(cells=CELLS, lid='+y', plain=('-y',), cuts=VENTS, adds=RIBS), color='#c9884a',
    refs=[('board', 'GY-BME280', bme280(at=BOARD))],
    notes=['Bo 15,4×11,6 mm chỉ chừa 0,4 mm hai bên; hãy đo bo của bạn, nếu lớn hơn thì cần khối 2×1×1.',
           'Không còn chỗ cho đầu cắm Dupont: hàn dây trực tiếp vào bo.',
           'Mặt −y trơn có ba khe thoáng để cảm biến đo không khí ngoài.'])
```

- [ ] **Step 2: Build and fix**

```bash
uv run python -c "from printkit.cli import placeholder_png; open('models/kit-bme280/thumbnail.png','wb').write(placeholder_png())"
uv run printkit cad kit-bme280
```
Expected: `kit-bme280: 2 print parts, 7 checks passed`. If the reference board clears the walls by less than the library demands, move the board in y or x; if it cannot fit, change the cells to `(2, 1, 1)` and say so in the README.

- [ ] **Step 3: README** (Task 4 outline). Board size 15.4 × 11.6 from listings (spec A3).

- [ ] **Step 4: Verify** dimensions `[19.8, 19.8, 19.8]` in `model.json`.

- [ ] **Step 5: Commit**

```bash
git add models/kit-bme280
git commit -m "Add kit-bme280: climate sensor module"
```

---

### Task 8: `kit-mpu6050` (Module cảm biến MPU6050)

**Files:** Create `models/kit-mpu6050/model.py`, `README.md`, `thumbnail.png` (placeholder).

**Interfaces:** consumes `printkit.library.electronics.mpu6050`; produces id `kit-mpu6050`.

- [ ] **Step 1: Write the model**

```python
"""Module cảm biến MPU6050: 2 x 2 x 1 units. GY-521 board on four posts, lid on top. Millimetres, Z up."""
import itertools

from printkit.library.electronics import mpu6050
from printkit.modules import WALL, ModuleSpec, bounds, cyl, kit_model

CELLS = (2, 2, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+z'))
CX, CY = (LO[0] + HI[0]) / 2, (LO[1] + HI[1]) / 2
FLOOR = LO[2] + WALL
BOARD = (CX, CY, 6.0)                                  # PCB underside; the header body (2.5 mm) hangs under it
POSTS = tuple(cyl((CX + sx, CY + sy, FLOOR - 0.5), (0, 0, 1), 1.2, BOARD[2] - FLOOR + 0.5)
              for sx, sy in itertools.product((-8, 8), (-2, 2)))

model = kit_model(
    'kit-mpu6050', title='Module cảm biến MPU6050',
    description='Cảm biến gia tốc và con quay GY-521 MPU6050 trong khối 2×2×1.',
    spec=ModuleSpec(cells=CELLS, lid='+z', adds=POSTS), color='#d06a6a',
    refs=[('board', 'GY-521 MPU6050', mpu6050(at=BOARD))],
    notes=['Bo khoảng 20,5×16 mm theo trang bán hàng, các nơi ghi 20×16 đến 21×16,4; đo bo của bạn.',
           'Đặt bo đúng hướng trục khi dán lên trụ: trục X của chip dọc theo chiều dài bo.',
           'Hàn dây trực tiếp hoặc dùng dải chân cắm ngắn; khoảng trống trên bo là 9 mm.'])
```

- [ ] **Step 2: Build and fix**

```bash
uv run python -c "from printkit.cli import placeholder_png; open('models/kit-mpu6050/thumbnail.png','wb').write(placeholder_png())"
uv run printkit cad kit-mpu6050
```
Expected: `kit-mpu6050: 2 print parts, 7 checks passed`. The posts must stay inside the PCB outline (x ±8 of 20.5, y ±2 of 16).

- [ ] **Step 3: README** (Task 4 outline).

- [ ] **Step 4: Verify** dimensions `[39.8, 39.8, 19.8]`.

- [ ] **Step 5: Commit**

```bash
git add models/kit-mpu6050
git commit -m "Add kit-mpu6050: IMU sensor module"
```

---

### Task 9: `kit-pir` (Module cảm biến PIR)

**Files:** Create `models/kit-pir/model.py`, `README.md`, `thumbnail.png` (placeholder).

**Interfaces:** consumes `printkit.library.electronics.hc_sr501`; produces id `kit-pir`.

- [ ] **Step 1: Write the model**

```python
"""Module cảm biến PIR: 2 x 2 x 2 units. HC-SR501 hangs from the ceiling, its lens passes through a hole in the +z face. Millimetres, Z up."""
import itertools

from printkit.library.electronics import hc_sr501
from printkit.modules import WALL, ModuleSpec, bounds, cyl, kit_model

CELLS = (2, 2, 2)
LO, HI = bounds(ModuleSpec(CELLS, '-z'))
CX, CY = (LO[0] + HI[0]) / 2, (LO[1] + HI[1]) / 2
LENS_TOP = HI[2] - 0.9                                 # the lens ends 0.9 mm under the outer top face
BOARD = (CX, CY, LENS_TOP - 19.2)                      # PCB underside; PCB 1.2 thick plus 18 mm lens
CEILING = HI[2] - WALL
HOLE = cyl((CX, CY, HI[2] - WALL - 1), (0, 0, 1), 12.2, WALL + 2)          # O24.4 for the O23 lens
HANGERS = tuple(cyl((CX + sx, CY + sy, BOARD[2] + 1.2), (0, 0, 1), 1.5, CEILING + 0.5 - (BOARD[2] + 1.2))
                for sx, sy in itertools.product((-13, 13), (-9, 9)))

model = kit_model(
    'kit-pir', title='Module cảm biến PIR',
    description='Cảm biến chuyển động HC-SR501, thấu kính nhô qua lỗ ở mặt trên, khối 2×2×2.',
    spec=ModuleSpec(cells=CELLS, lid='-z', plain=('+z',), cuts=(HOLE,), adds=HANGERS), color='#4d9d7a',
    refs=[('board', 'HC-SR501', hc_sr501(at=BOARD))],
    notes=['Bo 32×24 mm, thấu kính Ø23; chiều cao các trang bán hàng ghi 18 đến 30 mm không khớp nhau, hãy đo.',
           'Mặt +z là cửa sổ cho thấu kính nên không có điểm nối.',
           'Bo treo vào bốn trụ từ trần; lắp từ phía nắp −z rồi đóng nắp.'])
```

- [ ] **Step 2: Build and fix**

```bash
uv run python -c "from printkit.cli import placeholder_png; open('models/kit-pir/thumbnail.png','wb').write(placeholder_png())"
uv run printkit cad kit-pir
```
Expected: `kit-pir: 2 print parts, 7 checks passed`. The lens (a reference `Solid`) must clear the hole; if the clearance check complains, enlarge the hole radius, not the lens.

- [ ] **Step 3: README** (Task 4 outline).

- [ ] **Step 4: Verify** dimensions `[39.8, 39.8, 39.8]`.

- [ ] **Step 5: Commit**

```bash
git add models/kit-pir
git commit -m "Add kit-pir: PIR motion sensor module"
```

---

### Task 10: Retire V1 and V2, re-base the catalog and tests

**Files:**
- Delete: `models/esp32-c3-supermini/`, `models/esp32-c3-supermini-18650/` (`git rm -r`)
- Modify: `models.json`, `README.md`, `tests/test_catalog.py`, `tests/model-core.test.js`
- Reason (Chesterton): V1 and V2 were one-off enclosures superseded by the kit; git history keeps them; the tests only used them as sample data.

- [ ] **Step 1: Write `models.json`**

```json
[
  "models/kit-esp32/model.json",
  "models/kit-battery/model.json",
  "models/kit-display/model.json",
  "models/kit-bme280/model.json",
  "models/kit-mpu6050/model.json",
  "models/kit-pir/model.json",
  "models/ps4-wraeclast-stand/model.json"
]
```

- [ ] **Step 2: Delete the old models and see which tests break**

```bash
git rm -r -q models/esp32-c3-supermini models/esp32-c3-supermini-18650
uv run pytest -q 2>&1 | tail -20
node --test tests/*.test.js 2>&1 | tail -20
```
Expected: failures only in `tests/test_catalog.py` and `tests/model-core.test.js` (they name the deleted ids).

- [ ] **Step 3: Re-base `tests/test_catalog.py`.** In the file: replace `"esp32-c3-supermini-18650"` with `"kit-esp32"` everywhere (fixture `battery_model`, `broken_catalog`, `test_catalog_errors_start_with_manifest_path`); change `test_all_models` to `assert {"kit-esp32", "kit-battery", "kit-display", "kit-bme280", "kit-mpu6050", "kit-pir"} <= {model["id"] for _, model in load_catalog()}`. The test that edits `measurements[0]["variants"]` has no `variants` in a kit model: in that test first add `model["measurements"][0]["variants"] = [{"whenHidden": "lid", "lines": model["measurements"][0]["lines"]}]`, then keep the existing assertion on the mismatched line count. The drag-axis test uses `parts[1]["drag"]`; part 1 of a kit model is `lid` and has a drag, so it works unchanged. Run `uv run pytest tests/test_catalog.py -q` until green.

- [ ] **Step 4: Re-base `tests/model-core.test.js`.** Replace `const battery = load('esp32-c3-supermini-18650'); const small = load('esp32-c3-supermini');` with `const esp32 = load('kit-esp32'); const battery = load('kit-battery');`; in the animation test iterate `[esp32, battery]`; rewrite the test "battery replacement opens its lid before lifting the cell; other parts stay home" as "opening the lid lifts it and its fasteners; other parts stay home" using `animation = battery.animations.find(item => item.id === 'open')`, asserting that at time 0.4 the `lid` offset is non-zero and that every part not in `animation.tracks` has a zero offset; the "sliced models ship toolpaths" test iterates ids from `models.json` whose `model.json` has a `print` key (none until Task 11 slices them, so after Task 11 it covers all six kit ids). Run `node --test tests/*.test.js` until green.

- [ ] **Step 5: Update `README.md`.** In the folder-structure block add `printkit/modules.py   Chuẩn module: đơn vị 20 mm, điểm nối, vỏ, nắp, kiểm tra` and under the list of commands add a section "## Module" with: the unit size, `+`/`−` face rule, that every connector pocket is as deep as its part, and `uv run printkit cad kit-esp32` as the build example. Remove nothing else.

- [ ] **Step 6: Full run**

Run: `uv run pytest -q && node --test tests/*.test.js`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add -A models.json README.md tests models
git commit -m "Retire V1 and V2 enclosures; the catalog and tests run on the kit modules"
```

---

### Task 11: Thumbnails, slicing, offline bundles, final verification, cleanup

**Files:**
- Create: `models/kit-*/thumbnail.png` (6 real 960 × 720 PNGs)
- Generated: `models/kit-*/print/*.gcode.3mf`, `print/layers.json`, `models/kit-*/kit-*.zip`
- Delete: `docs/superpowers/explore/` (the spike and its sheets; the design now lives in `printkit/modules.py` and the spec)

- [ ] **Step 1: Slice every module with Bambu Studio**

```bash
for id in kit-esp32 kit-battery kit-display kit-bme280 kit-mpu6050 kit-pir; do uv run printkit slice $id; done
```
Expected: each prints `<id>: sliced <n> layers · <g> g · <min> min (Bambu Studio …)`. A module that fails to slice is reported with its error; do not retry blindly: read the error, fix the module, rerun.

- [ ] **Step 2: Serve the app and capture thumbnails**

```bash
(python3 -m http.server 8765 >/tmp/kit-server.log 2>&1 &) ; sleep 1
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for id in kit-esp32 kit-battery kit-display kit-bme280 kit-mpu6050 kit-pir; do
  "$CHROME" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist --hide-scrollbars \
    --window-size=1280,720 --virtual-time-budget=20000 --screenshot=/tmp/$id.png "http://localhost:8765/#model/$id"
done
```
Look at each `/tmp/<id>.png`. The model must be visible and not cropped. Crop each to the 3D canvas and resize to 960 × 720:

```bash
uv run python - <<'EOF'
from PIL import Image
for id in ['kit-esp32','kit-battery','kit-display','kit-bme280','kit-mpu6050','kit-pir']:
    im = Image.open(f'/tmp/{id}.png'); w, h = im.size
    im.crop((0, 0, int(w * 0.75), h)).resize((960, 720)).save(f'models/{id}/thumbnail.png')
EOF
```
If PIL is missing, use `sips -s format png --cropToHeightWidth 720 960 /tmp/<id>.png --out models/<id>/thumbnail.png`. Check the crop fraction by viewing one image; adjust once.

- [ ] **Step 3: Package the offline bundles**

Run: `uv run printkit build`
Expected: no error; `models/<id>/<id>.zip` exists for every model in `models.json`. (`slice` already ran `cad`, so no rebuild is needed; the thumbnails are plain assets.)

- [ ] **Step 4: Verify the website end to end**

```bash
uv run pytest -q && node --test tests/*.test.js
"$CHROME" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist --hide-scrollbars --window-size=1400,900 --virtual-time-budget=20000 --screenshot=/tmp/gallery.png "http://localhost:8765/"
"$CHROME" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist --hide-scrollbars --window-size=1400,900 --virtual-time-budget=20000 --screenshot=/tmp/print.png "http://localhost:8765/#print/kit-battery"
pkill -f "http.server 8765"
```
Expected: tests pass; `/tmp/gallery.png` shows seven cards (six modules and the PS4 stand) with thumbnails; `/tmp/print.png` shows the print simulation of `kit-battery`. View both images.

- [ ] **Step 5: Remove the spike**

```bash
rm -rf docs/superpowers/explore    # untracked scratch, never committed
git status --short | head
```
Expected: no leftover untracked `docs/superpowers/explore`. The spec stays.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Slice and package the kit modules, add thumbnails, remove the exploration sheets"
```
