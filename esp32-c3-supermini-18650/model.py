"""V2: removable 18650 + ESP32-C3 SuperMini + TPS63020 reference module.

All units mm. Run with CadQuery 2.8.0 and trimesh 5.1.1.
Hardware envelopes are assumptions; see README before printing.
"""
import base64
import json
from pathlib import Path

import cadquery as cq
import trimesh

OUT = Path(__file__).resolve().parent
W, L, FLOOR, WALL, BASE_H, CAP_T = 60.0, 84.0, 2.0, 2.0, 25.4, 1.8
HEIGHT = BASE_H + CAP_T
DIVIDER_X = -1.5
ESP_X, ESP_Y, ESP_Z = 14.0, -26.5, 12.0
CELL_X, CELL_Z, CELL_D, CELL_L = -16.5, 13.1, 18.5, 65.3
FIT, SKIRT_H, EPS = .2, 2.4, .02
USB_BOTTOM, USB_W = ESP_Z-.8, 14.0
USB_CAP_FACE_T, USB_CAP_DEPTH = 1.2, 1.7
USB_CAP_CENTER_Z = (USB_BOTTOM+BASE_H)/2
USB_CAP_FRONT_Y = -L/2-USB_CAP_FACE_T
LIDS = {
    "battery_lid": {"center": -15.8, "cavity_center": -15.25, "cavity_width": 25.5},
    "electronics_lid": {"center": 14.3, "cavity_center": 13.75, "cavity_width": 28.5},
}


def block(w, length, height, x=0, y=0, z=0):
    return cq.Workplane("XY").box(w, length, height, centered=(True, True, False)).translate((x, y, z))


def rounded(w, length, height, radius, x=0, y=0, z=0):
    return block(w, length, height, x, y, z).edges("|Z").fillet(radius)


def make_base():
    base = rounded(W, L, BASE_H, 4).cut(rounded(W-2*WALL, L-2*WALL, BASE_H, 2, z=FLOOR))
    divider = block(2, L-2*WALL+EPS, BASE_H, x=DIVIDER_X)
    divider = divider.cut(block(4, 8, 6, x=DIVIDER_X, y=-8, z=4))
    base = base.union(divider)
    # Four supports lie inside the header rows. No board mounting holes assumed.
    for x in (-4.6, 4.6):
        for y in (-7.4, 7.4):
            post = cq.Workplane("XY").circle(1.5).extrude(ESP_Z)
            base = base.union(post.translate((ESP_X+x, ESP_Y+y, 0)))
    for x in (-10.35, 10.35):
        for y in (-6.1, 6.1):
            base = base.union(block(2.2, 2.2, ESP_Z+1.6, ESP_X+x, ESP_Y+y))
    base = base.union(block(8, 2, ESP_Z+1.6, ESP_X, ESP_Y+12.55))
    for x in (-6.8, 6.8):
        base = base.union(block(2.8, 2, ESP_Z+1.6, ESP_X+x, ESP_Y-12.55))
    # Holder envelope 75 x 22 x 18; adhesive allowance below it is 0.8 mm.
    for y in (-38.3, 38.3):
        base = base.union(block(16, 1, 6, CELL_X, y))
    for y in (-26, 26):
        base = base.union(block(1, 10, 6, -4.7, y))
    # TPS63020 supports plus 0.5 mm adhesive; reserve 35 x 24 mm footprint.
    for x in (5, 23):
        base = base.union(block(2.2, 30, 5.5, x, 14))
    for x in (1.2, 26.8):
        for y in (3, 25):
            base = base.union(block(1, 5, 8, x, y))
    for y in (-4.1, 32.1):
        base = base.union(block(12, 1, 8, 14, y))
    base = base.cut(block(USB_W, 10, BASE_H, ESP_X, -L/2, USB_BOTTOM))
    # Fingernail recess under the removable battery cover.
    base = base.cut(block(8, 4, 1.1, CELL_X, -L/2, BASE_H-1))
    return base.clean()


def installed_lid(name, ribs=True):
    spec = LIDS[name]
    plate = rounded(W, L, CAP_T, 4, z=BASE_H)
    if name == "battery_lid":
        plate = plate.intersect(block(100, 100, 50, x=-51.6))
    else:
        plate = plate.intersect(block(100, 100, 50, x=48.6))
    cx, cw = spec["cavity_center"], spec["cavity_width"]
    skirt = rounded(cw-2*FIT, 80-2*FIT, SKIRT_H+EPS, 1.6, x=cx, z=BASE_H-SKIRT_H)
    skirt = skirt.cut(rounded(cw-2*(FIT+1.2), 80-2*(FIT+1.2), SKIRT_H+3*EPS,
                              .5, x=cx, z=BASE_H-SKIRT_H-EPS))
    if name == "electronics_lid":
        skirt = skirt.cut(block(14.6, 6, SKIRT_H+EPS, ESP_X, -40, BASE_H-SKIRT_H))
        for y in (20, 23, 26):
            vent = cq.Workplane("XY").slot2D(12, 1.4).extrude(CAP_T+2*EPS)
            plate = plate.cut(vent.translate((14, y, BASE_H-EPS)))
    else:
        # Shallow tactile grooves, no through openings above the cell.
        for y in (-28, -25, -22):
            plate = plate.cut(block(12, 1.2, .5, CELL_X, y, HEIGHT-.4))
    lid = plate.union(skirt)
    if ribs:
        for side in (-1, 1):
            for y in (-24, 24):
                rib = cq.Workplane("XY").circle(.35).extrude(SKIRT_H+EPS)
                lid = lid.union(rib.translate((cx+side*(cw/2-.27), y, BASE_H-SKIRT_H)))
    return lid.clean()


def installed_usb_cap(ribs=True):
    """Removable cover gripping the enclosure opening, clear of the USB socket."""
    opening_h = BASE_H-USB_BOTTOM
    face = block(USB_W+3, USB_CAP_FACE_T, opening_h+3,
                 ESP_X, -L/2-USB_CAP_FACE_T/2, USB_BOTTOM-1.5).edges("|Y").fillet(.8)
    tongue = block(USB_W-2*FIT, USB_CAP_DEPTH+EPS, opening_h-2*FIT,
                   ESP_X, -L/2+(USB_CAP_DEPTH-EPS)/2, USB_BOTTOM+FIT).edges("|Y").fillet(.5)
    cap = face.union(tongue)
    if ribs:
        for side in (-1, 1):
            for z in (USB_CAP_CENTER_Z-3, USB_CAP_CENTER_Z+3):
                rib = cq.Workplane("XY").circle(.28).extrude(1.2+EPS)
                rib = rib.rotate((0,0,0), (1,0,0), -90)
                cap = cap.union(rib.translate((ESP_X+side*(USB_W/2-FIT), -L/2-EPS, z)))
    return cap.clean()


def reference_board():
    """Approximate board only: component locations are illustrative, not measured."""
    PCB_W, PCB_L, PCB_T, PCB_Z = 18.0, 22.5, 1.6, ESP_Z
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


def reference_parts():
    refs = [("board", name, shape.translate((ESP_X, ESP_Y, 0)), color)
            for name, shape, color in reference_board()]
    holder = block(22, 75, 1, CELL_X, z=2.8)
    for x in (-10.45, 10.45):
        holder = holder.union(block(1.1, 75, 8, CELL_X+x, z=2.8))
    for y in (-35.75, 35.75):
        holder = holder.union(block(22, 3.5, 18, CELL_X, y, 2.8))
    refs.append(("holder", "holder", holder, "#303d46"))
    cell = cq.Workplane("XY").circle(CELL_D/2).extrude(CELL_L)
    cell = cell.rotate((0, 0, 0), (1, 0, 0), 90).translate((CELL_X, CELL_L/2, CELL_Z))
    refs.append(("cell", "cell", cell, "#87b483"))
    refs += [("converter", "module_pcb", block(24, 34, 1, 14, 14, 6), "#27729a"),
             ("converter", "inductor", block(7, 7, 3.5, 14, 13, 7), "#485760"),
             ("converter", "regulator", block(4, 4, 1.2, 14, 22, 7), "#202c34")]
    for x in (5, 23):
        for y in (1, 27):
            refs.append(("converter", f"pad_{x}_{y}", block(3, 4, .1, x, y, 7), "#cba35e"))
    return refs


def overlap(a, b):
    return a.intersect(b).val().Volume()


def export_and_verify():
    base = make_base()
    lids = {name: installed_lid(name) for name in LIDS}
    usb_cap = installed_usb_cap()
    refs = reference_parts()
    report = {"units": "mm", "outer_dimensions": [W, L, HEIGHT],
              "outer_dimensions_with_usb_cap": [W, L+USB_CAP_FACE_T, HEIGHT],
              "usb_cap": {"opening": [USB_W, BASE_H-USB_BOTTOM], "insert_depth": USB_CAP_DEPTH,
                          "clearance_per_side": FIT, "rib_interference": .08,
                          "installed_origin": [ESP_X, USB_CAP_FRONT_Y, USB_CAP_CENTER_Z]},
              "reference_envelopes": {"holder": [22,75,18], "cell_diameter_length": [CELL_D,CELL_L],
                                      "converter": [24,34,4.5], "pcb": [18,22.5,1.6]},
              "parts": {}, "checks": {"physical_fit_tested": False,
              "exact_shopee_variant_verified": False}}
    printable = {"base": base}
    for name, lid in lids.items():
        printable[name] = lid.translate((-LIDS[name]["center"], 0, -HEIGHT)).rotate((0,0,0), (0,1,0), 180)
    printable["usb_cap"] = usb_cap.translate((-ESP_X, -USB_CAP_FRONT_Y, -USB_CAP_CENTER_Z)).rotate((0,0,0), (1,0,0), 90)
    for name, shape in printable.items():
        assert shape.val().isValid() and len(shape.solids().vals()) == 1, name
        cq.exporters.export(shape, str(OUT/f"{name}.stl"), tolerance=.03, angularTolerance=.1)
        mesh = trimesh.load_mesh(OUT/f"{name}.stl")
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
        assert len(mesh.split()) == 1, name
        report["parts"][name] = {"watertight": True, "solid_count": 1,
                                 "bounds_mm": mesh.bounds.round(3).tolist(), "volume_mm3": round(mesh.volume,2)}
    for name in lids:
        assert overlap(base, installed_lid(name, False)) < 1e-6, f"Base intersects {name} without ribs"
    assert overlap(*lids.values()) < 1e-6, "Lids overlap"
    # Check the whole rectangular converter envelope, not just the drawn components.
    envelopes = [(name, shape) for _, name, shape, _ in refs]
    envelopes += [("module_envelope", block(24,34,4.5,14,14,6)),
                  ("holder_envelope", block(22,75,18,CELL_X,z=2.8))]
    for name, shape in envelopes:
        for case_name, case in {"base": base, **lids, "usb_cap": usb_cap}.items():
            assert overlap(case, shape) < 1e-6, f"{case_name} intersects {name}"
    assert overlap(base, installed_usb_cap(False)) < 1e-6, "USB cap tongue intersects base"
    for name, lid in lids.items():
        assert overlap(usb_cap, lid) < 1e-6, f"USB cap intersects {name}"
    # Swept bounding prisms cover every point of the cap during straight withdrawal.
    # Intentional friction ribs are omitted, as in the installed-fit test.
    travel = 24
    face_sweep = block(USB_W+3, USB_CAP_FACE_T+travel, BASE_H-USB_BOTTOM+3,
                       ESP_X, -L/2-(USB_CAP_FACE_T+travel)/2, USB_BOTTOM-1.5)
    tongue_sweep = block(USB_W-2*FIT, USB_CAP_DEPTH+EPS+travel, BASE_H-USB_BOTTOM-2*FIT,
                         ESP_X, -L/2+(USB_CAP_DEPTH-EPS-travel)/2, USB_BOTTOM+FIT)
    cap_sweep = face_sweep.union(tongue_sweep)
    for name, obstacle in {"base": base, **lids}.items():
        assert overlap(cap_sweep, obstacle) < 1e-6, f"USB cap withdrawal blocked by {name}"
    cell = next(shape for _, name, shape, _ in refs if name == "cell")
    holder = next(shape for _, name, shape, _ in refs if name == "holder")
    # Continuous vertical swept envelope contains every point during extraction.
    sweep = cell.union(cell.translate((0,0,45))).union(block(CELL_D,CELL_L,45,CELL_X,z=CELL_Z))
    for name, obstacle in (("base",base),("holder",holder),("electronics_lid",lids["electronics_lid"])):
        assert overlap(sweep, obstacle) < 1e-6, f"Battery removal blocked by {name}"
    cable = block(12, 12, 6, ESP_X, -44, ESP_Z+1.6-1.4)
    # Cable access is checked with the removable cap taken out.
    for name, case in {"base": base, **lids}.items():
        assert overlap(case,cable) < 1e-6, f"USB cable blocked by {name}"
    assembly = cq.Assembly(name="esp32_c3_supermini_18650")
    usb_socket = next(shape for _, name, shape, _ in refs if name == "usb")
    usb_gap = usb_socket.val().BoundingBox().ymin-usb_cap.val().BoundingBox().ymax
    assert usb_gap > 1, "USB cap too close to board socket"
    report["usb_cap"]["socket_clearance"] = round(usb_gap, 3)
    for name, part in {"base": base, **lids, "usb_cap": usb_cap}.items():
        assembly.add(part, name=name)
    assembly.export(str(OUT/"enclosure.step"))
    reimport = cq.importers.importStep(str(OUT/"enclosure.step"))
    assert len(reimport.solids().vals()) == 4 and all(s.isValid() for s in reimport.solids().vals())
    report["checks"].update(reference_envelopes_clear=True, lid_without_ribs_clear=True,
        independent_lids_clear=True, continuous_battery_removal_clear=True, usb_12x6_clear=True,
        usb_cap_without_ribs_clear=True, continuous_usb_cap_withdrawal_clear=True,
        usb_cap_clears_board_socket=True, step_four_valid_solids=True)
    # Reference meshes are embedded in the viewer and are not parts to print.
    assets = []
    for group, name, shape, color in refs:
        path = OUT/f".reference-{name}.stl"
        cq.exporters.export(shape, str(path), tolerance=.04, angularTolerance=.15)
        assets.append({"group":group,"name":name,"color":color,"stl":base64.b64encode(path.read_bytes()).decode()})
        path.unlink()
    (OUT/"reference.json").write_text(json.dumps(assets,separators=(",",":")))
    (OUT/"verification.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    export_and_verify()
