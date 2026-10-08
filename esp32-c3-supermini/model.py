"""ESP32-C3 SuperMini enclosure; millimetres, USB on the negative Y side.

Run: uv run --python 3.12 --with cadquery==2.8.0 --with trimesh model.py
"""

import json
from pathlib import Path

import cadquery as cq
import trimesh

OUT = Path(__file__).resolve().parent
PCB_W, PCB_L, PCB_T = 18.0, 22.5, 1.6
OUTER_W, OUTER_L = 26.4, 32.0
WALL, FLOOR, LID_T = 1.8, 1.8, 1.8
HEADER_SPACE = 10.0
PCB_Z = FLOOR + HEADER_SPACE
BASE_H = PCB_Z + PCB_T + 5.0
INNER_W, INNER_L = OUTER_W - 2 * WALL, OUTER_L - 2 * WALL
CORNER_R = 3.0
FIT = 0.20
SKIRT_H, SKIRT_WALL = 2.4, 1.2
USB_W, USB_BOTTOM = 14.0, PCB_Z - 0.8
EPS = 0.02


def block(w, length, height, x=0, y=0, z=0):
    return cq.Workplane("XY").box(w, length, height, centered=(True, True, False)).translate((x, y, z))


def rounded(w, length, height, radius, z=0):
    return block(w, length, height, z=z).edges("|Z").fillet(radius)


def make_base():
    shell = rounded(OUTER_W, OUTER_L, BASE_H, CORNER_R)
    cavity = rounded(INNER_W, INNER_L, BASE_H, CORNER_R - WALL, FLOOR)
    shell = shell.cut(cavity)
    # Supports stay inside the 15.24 mm header spacing, clear of the plastic strips.
    for x in (-4.6, 4.6):
        for y in (-7.4, 7.4):
            post = cq.Workplane("XY").circle(1.5).extrude(HEADER_SPACE + EPS)
            shell = shell.union(post.translate((x, y, FLOOR - EPS)))
    for side in (-1, 1):
        for y in (-6.1, 6.1):
            shell = shell.union(block(2.2, 2.2, PCB_Z + PCB_T, x=side * 10.35, y=y))
    shell = shell.union(block(8, 2.75, PCB_Z + PCB_T, y=12.875))
    for x in (-6.8, 6.8):
        shell = shell.union(block(2.8, 2.75, PCB_Z + PCB_T, x=x, y=-12.875))
    # Cut after the locating stops so they cannot obstruct the cable overmould.
    shell = shell.cut(block(USB_W, 8, BASE_H, y=-OUTER_L / 2, z=USB_BOTTOM))
    return shell.clean()


def make_lid(with_ribs=True):
    # The printed lid lies exterior-face down; its skirt grows upward.
    lid = rounded(OUTER_W, OUTER_L, LID_T, CORNER_R)
    skirt = rounded(INNER_W - 2 * FIT, INNER_L - 2 * FIT, SKIRT_H + EPS, 1.0, LID_T - EPS)
    skirt = skirt.cut(rounded(INNER_W - 2 * (FIT + SKIRT_WALL),
                               INNER_L - 2 * (FIT + SKIRT_WALL),
                               SKIRT_H + 2 * EPS, 0.6, LID_T - 2 * EPS))
    # Interrupt the front skirt so the cable opening remains unobstructed.
    skirt = skirt.cut(block(USB_W + 0.6, 7, SKIRT_H + 2 * EPS,
                             y=-INNER_L / 2, z=LID_T - EPS))
    lid = lid.union(skirt)
    if with_ribs:
        for side in (-1, 1):
            for y in (-6.5, 6.5):
                rib = cq.Workplane("XY").circle(0.35).extrude(SKIRT_H + EPS)
                # 0.08 mm local interference; fit must be calibrated on a print.
                lid = lid.union(rib.translate((side * (INNER_W / 2 - 0.27), y, LID_T - EPS)))
    for y in (-3.2, 0, 3.2):
        vent = cq.Workplane("XY").slot2D(12, 1.4).extrude(LID_T + 2 * EPS)
        lid = lid.cut(vent.translate((0, y, -EPS)))
    return lid.clean()


def installed_lid(lid):
    return lid.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, BASE_H + LID_T))


def reference_board():
    """Approximate board only: component locations are illustrative, not measured."""
    pieces = [("pcb", block(PCB_W, PCB_L, PCB_T, z=PCB_Z), "#214f55")]
    usb = block(9, 7.2, 3.2, y=-9.15, z=PCB_Z + PCB_T)
    pieces += [("usb", usb, "#c3cbd0"),
               ("chip", block(5, 5, 1, z=PCB_Z + PCB_T), "#24343c"),
               ("antenna", block(2.5, 3.4, 1.2, x=4.3, y=7.9, z=PCB_Z + PCB_T), "#d2bda0")]
    for side in (-1, 1):
        pieces.append((f"header_{side}", block(2.54, 20.32, 2.5,
                       x=side * 7.62, z=PCB_Z - 2.5), "#27343c"))
        for i in range(8):
            pieces.append((f"pin_{side}_{i}", block(0.64, 0.64, 11.5,
                           x=side * 7.62, y=(i - 3.5) * 2.54, z=PCB_Z - 8.5), "#c99b49"))
    return pieces


def overlap_volume(a, b):
    return a.intersect(b).val().Volume()


def export_and_verify():
    base, lid = make_base(), make_lid()
    summary = {"units": "mm", "outer_dimensions": [OUTER_W, OUTER_L, BASE_H + LID_T],
               "pcb_assumption": [PCB_W, PCB_L, PCB_T], "space_below_pcb": HEADER_SPACE,
               "lid_clearance_per_side": FIT, "rib_interference": 0.08, "parts": {}}
    for name, part in (("base", base), ("lid", lid)):
        assert part.val().isValid(), f"Invalid BRep: {name}"
        assert len(part.solids().vals()) == 1, f"Disconnected solid: {name}"
        path = OUT / f"{name}.stl"
        cq.exporters.export(part, str(path), tolerance=0.03, angularTolerance=0.1)
        mesh = trimesh.load_mesh(path)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
        assert len(mesh.split()) == 1, f"Disconnected mesh: {name}"
        summary["parts"][name] = {"watertight": True, "solid_count": 1,
                                 "volume_mm3": round(mesh.volume, 2),
                                 "bounds_mm": mesh.bounds.round(3).tolist()}
    # Normal mating surfaces must clear; intentional friction ribs are excluded here.
    assert overlap_volume(base, installed_lid(make_lid(False))) < 1e-6
    closed = installed_lid(lid)
    reference = reference_board()
    for name, shape, _ in reference:
        assert overlap_volume(base, shape) < 1e-6, f"Base collides with {name}"
        assert overlap_volume(closed, shape) < 1e-6, f"Lid collides with {name}"
    cable = block(12, 10, 6, y=-17.5, z=PCB_Z + PCB_T - 1.4)
    assert overlap_volume(base, cable) < 1e-6, "Cable blocked by base"
    assert overlap_volume(closed, cable) < 1e-6, "Cable blocked by lid"
    summary["checks"] = {"reference_board_and_headers_clear": True,
                         "lid_without_friction_ribs_clears_base": True,
                         "cable_envelope_12x6_clear": True,
                         "physical_fit_tested": False}
    assembly = cq.Assembly(name="esp32_c3_supermini_enclosure")
    assembly.add(base, name="base", color=cq.Color(0.16, 0.48, 0.54))
    assembly.add(closed, name="lid", color=cq.Color(0.89, 0.87, 0.82))
    assembly.export(str(OUT / "enclosure.step"))
    (OUT / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return base, lid, reference


if __name__ == "__main__":
    export_and_verify()
