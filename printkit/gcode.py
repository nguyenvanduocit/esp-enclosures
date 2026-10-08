"""Bambu Studio G-code → per-layer toolpath polylines for the viewer's print preview. Pure."""

import math

UNIT = 100  # coordinates are stored as integers in 0.01 mm
TYPES = [
    ("outer_wall", "Thành ngoài", "#f2b56b"),
    ("inner_wall", "Thành trong", "#e3895f"),
    ("overhang", "Thành treo", "#ff5d73"),
    ("infill", "Infill", "#8f7ae5"),
    ("solid", "Lớp đặc", "#5aa7e8"),
    ("bridge", "Cầu", "#4fd1c5"),
    ("support", "Support", "#c3ccd2"),
    ("gap", "Lấp khe", "#f5e663"),
    ("brim", "Brim / skirt", "#9ccc65"),
    ("other", "Khác", "#7a8288"),
]
FEATURES = {
    "Outer wall": "outer_wall",
    "Inner wall": "inner_wall",
    "Overhang wall": "overhang",
    "Sparse infill": "infill",
    "Internal solid infill": "solid",
    "Top surface": "solid",
    "Bottom surface": "solid",
    "Bridge": "bridge",
    "Support": "support",
    "Support interface": "support",
    "Support transition": "support",
    "Gap infill": "gap",
    "Brim": "brim",
    "Skirt": "brim",
}
MOVES = ("G0", "G1", "G2", "G3")


def arc_points(start, end, center, clockwise, step_deg=10):
    """Points along a G2 (clockwise) or G3 arc from `start` to `end`, excluding `start`."""
    (sx, sy), (ex, ey), (cx, cy) = start, end, center
    a0, a1 = math.atan2(sy - cy, sx - cx), math.atan2(ey - cy, ex - cx)
    sweep = a1 - a0
    if clockwise and sweep >= 0:
        sweep -= 2 * math.pi
    if not clockwise and sweep <= 0:
        sweep += 2 * math.pi
    radius = math.hypot(sx - cx, sy - cy)
    steps = max(1, math.ceil(abs(math.degrees(sweep)) / step_deg - 1e-9))
    points = [
        (
            cx + radius * math.cos(a0 + sweep * k / steps),
            cy + radius * math.sin(a0 + sweep * k / steps),
        )
        for k in range(1, steps)
    ]
    return points + [end]


def parse_layers(gcode, bed=(256, 256)):
    layers, layer, feature, path = [], None, "other", None
    x = y = None
    absolute = True
    for raw in gcode.splitlines():
        line = raw.strip()
        if line.startswith(";"):
            if line == "; CHANGE_LAYER":
                layer, path = {"z": None, "h": None, "paths": {}}, None
                layers.append(layer)
            elif layer is not None and line.startswith("; Z_HEIGHT:"):
                layer["z"] = float(line.split(":", 1)[1])
            elif layer is not None and line.startswith("; LAYER_HEIGHT:"):
                layer["h"] = float(line.split(":", 1)[1])
            elif line.startswith("; FEATURE:"):
                feature, path = (
                    FEATURES.get(line.split(":", 1)[1].strip(), "other"),
                    None,
                )
            continue
        words = line.split(";", 1)[0].split()
        if not words:
            continue
        command = words[0]
        if command in ("G90", "G91"):
            absolute = command == "G90"
            continue
        if command not in MOVES:
            continue
        params = {word[0]: float(word[1:]) for word in words[1:] if word[0] in "XYZEIJ"}
        if absolute:
            nx, ny = params.get("X", x), params.get("Y", y)
        else:
            nx, ny = (x or 0) + params.get("X", 0), (y or 0) + params.get("Y", 0)
        moved = (nx, ny) != (x, y) or command in ('G2', 'G3')  # a full-circle arc ends where it starts
        if layer is not None and x is not None and moved and params.get("E", 0) > 0:
            if command in ("G2", "G3"):
                center = (x + params.get("I", 0), y + params.get("J", 0))
                points = arc_points((x, y), (nx, ny), center, clockwise=command == "G2")
            else:
                points = [(nx, ny)]
            if path is None:
                path = [round(x * UNIT), round(y * UNIT)]
                layer["paths"].setdefault(feature, []).append(path)
            for px, py in points:
                path += [round(px * UNIT), round(py * UNIT)]
        elif moved:
            path = None
        x, y = nx, ny
    if any(item["z"] is None for item in layers):
        raise ValueError("a layer has no ; Z_HEIGHT marker")
    return {
        "bed": list(bed),
        "unit": 1 / UNIT,
        "types": [
            {"id": type_id, "label": label, "color": color}
            for type_id, label, color in TYPES
        ],
        "layers": layers,
    }
