"""Model declarations and their model.json rendering. No CAD or file I/O here."""

import math
from dataclasses import dataclass, field
from functools import cache

SCHEMA_VERSION = 1
MEASURE_COLORS = {"case": "#efb96e", "component": "#83caff"}


@dataclass(frozen=True)
class Drag:
    axis: tuple
    max_distance: float


@dataclass(frozen=True)
class Box:
    """Axis-aligned reference box; rendered as a viewer primitive."""

    name: str
    size: tuple
    center: tuple
    color: str


@dataclass(frozen=True)
class Solid:
    """Reference CadQuery solid; exported to reference/<name>.stl."""

    name: str
    shape: object
    color: str


@dataclass(frozen=True)
class PrintPart:
    id: str
    label: str
    color: str
    build: object
    drag: Drag | None
    print_rotation: tuple
    max_overhang_mm2: float | None


@dataclass(frozen=True)
class ReferencePart:
    id: str
    label: str
    pieces: tuple
    drag: Drag | None


PRINTER_LABEL = "Bambu Lab P1S · nozzle 0,4 mm"


@dataclass(frozen=True)
class Print:
    """Plate-wide slicer settings; slicer.process_settings maps them to Bambu Studio keys.

    `plate` is the build plate Studio heats for (the CLI ignores the printer's default bed type).
    `brim` is 'auto', 0 for no brim, or a width in mm for an outer brim. `extra` holds raw
    Bambu Studio process keys for anything the named fields do not cover."""

    layer: float = 0.16
    first_layer: float = 0.2
    walls: int = 2
    infill: tuple = (15, "grid")
    supports: bool = False
    brim: object = "auto"
    filament: str = "PLA"
    plate: str = "Textured PEI Plate"
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        valid = self.brim == "auto" or (
            isinstance(self.brim, (int, float)) and not isinstance(self.brim, bool) and self.brim >= 0
        )
        if not valid:
            raise ValueError(f"brim must be 'auto', 0 or a width in mm, got {self.brim!r}")


def vn(value):
    """Number in Vietnamese notation: 0.16 → '0,16'."""
    return f"{value:g}".replace(".", ",")


def print_rows(settings):
    density, pattern = settings.infill
    if settings.brim == "auto":
        brim = "Tự động"
    else:
        brim = f"{vn(settings.brim)} mm, viền ngoài" if settings.brim else "Không"
    rows = [
        ["Máy / nhựa", f"{PRINTER_LABEL} · {settings.filament}"],
        ["Bàn in", settings.plate],
        ["Layer / lớp đầu", f"{vn(settings.layer)} / {vn(settings.first_layer)} mm"],
        ["Thành", f"{settings.walls} vòng"],
        ["Infill", f"{vn(density)}% {pattern}"],
        ["Support", "Bật" if settings.supports else "Tắt"],
        ["Brim", brim],
    ]
    rows += [
        [key, vn(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)]
        for key, value in settings.extra.items()
    ]
    return rows


def duration_vn(seconds):
    hours, minutes = divmod(round(seconds / 60), 60)
    return f"{hours} giờ {minutes} phút" if hours else f"{minutes} phút"


def grams_vn(grams):
    return f"{vn(round(grams, 1))} g"


def slice_section(model, sliced):
    """Per-part rows are each part printed alone, so they do not sum to the plate row."""
    labels = {part.id: part.label for part in model.parts}
    rows = [
        [f"{labels[item['id']]} (in riêng)", f"{grams_vn(item['grams'])} · {duration_vn(item['seconds'])}"]
        for item in sliced["parts"]
    ]
    rows.append(["Cả bàn in", f"{grams_vn(sliced['grams'])} · {duration_vn(sliced['seconds'])} · {sliced['layerCount']} lớp"])
    return {
        "title": "Kết quả slice",
        "rows": rows,
        "notes": [
            f"{sliced['slicer']} với cấu hình ở trên. Số liệu từng chi tiết tính cho việc in riêng chi tiết đó "
            "(mỗi lần gồm nhựa và thời gian mồi/kết thúc), nên không cộng lại thành số của cả bàn in.",
            "Mở file .gcode.3mf trong Bambu Studio để xem preview hoặc gửi sang máy in.",
        ],
        "links": [],
    }


def dim(anchor_a, anchor_b, offset, name, label_offset=(0, 0, 0), prefix=""):
    """Measurement line drawn `offset` away from the two anchor points it measures."""
    length = math.dist(anchor_a, anchor_b)
    return {
        "a": [p + o for p, o in zip(anchor_a, offset)],
        "b": [p + o for p, o in zip(anchor_b, offset)],
        "anchorA": list(anchor_a),
        "anchorB": list(anchor_b),
        "label": f"{prefix}{length:g} mm · {name}",
        "labelOffset": list(label_offset),
    }


def pulse(value):
    """Keyframes that rest, move to `value`, hold, and return to rest."""
    rest = (0, 0, 0)
    return [(0, rest), (0.08, rest), (0.4, value), (0.72, value), (0.97, rest), (1, rest)]


def keyframes(frames):
    return [{"time": time, "value": list(value)} for time, value in frames]


class Model:
    def __init__(
        self,
        id,
        *,
        title,
        description,
        category,
        status,
        thumbnail,
        dimensions,
        camera,
        grid,
        print_info,
        print=Print(),
    ):
        self.id = id
        self.print_settings = print
        self.info = {
            "category": category,
            "status": status,
            "thumbnail": thumbnail,
            "title": title,
            "description": description,
            "dimensions": list(dimensions),
            "camera": camera,
            "grid": grid,
            "printInfo": print_info,
        }
        self.parts, self.measurements, self.animations, self.checks = [], [], [], []

    def part(
        self,
        id,
        label,
        *,
        color,
        drag=None,
        print_rotation=(0, 0, 0),
        max_overhang_mm2=None,
    ):
        """Register a printed part built in its installed pose; the build runs once."""

        def register(build):
            build = cache(build)
            self.parts.append(
                PrintPart(
                    id,
                    label,
                    color,
                    build,
                    drag,
                    tuple(print_rotation),
                    max_overhang_mm2,
                )
            )
            return build

        return register

    def reference(self, id, label, pieces, *, drag=None):
        self.parts.append(ReferencePart(id, label, tuple(pieces), drag))

    def measure(
        self,
        id,
        label,
        *,
        kind,
        follow,
        lines,
        visible_with=None,
        color=None,
        label_width=32,
        variants=None,
    ):
        item = {"id": id, "label": label, "kind": kind, "followPart": follow}
        if visible_with:
            item["visibleWith"] = visible_with
        item.update(
            color=color or MEASURE_COLORS[kind],
            labelWidth=label_width,
            lines=list(lines),
        )
        if variants:
            item["variants"] = [
                {"whenHidden": part, "lines": list(lines)}
                for part, lines in variants.items()
            ]
        self.measurements.append(item)

    def animation(
        self, id, label, *, duration, open_pose, tracks, camera, measure_reveal
    ):
        self.animations.append(
            {
                "id": id,
                "label": label,
                "duration": duration,
                "openPose": {part: list(offset) for part, offset in open_pose.items()},
                "tracks": [
                    {"part": part, "keyframes": keyframes(frames)}
                    for part, frames in tracks.items()
                ],
                "camera": keyframes(camera),
                "measureReveal": list(measure_reveal),
            }
        )

    def check(self, name):
        """Register a design check; it raises CheckFailed or returns measured values."""

        def register(check):
            self.checks.append((name, check))
            return check

        return register


def clean(value):
    if isinstance(value, float):
        return round(value, 6) + 0.0
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return value


def _meshes(part):
    if isinstance(part, PrintPart):
        return [{"src": f"{part.id}.stl", "color": part.color}]
    return [
        {
            "primitive": "box",
            "size": list(piece.size),
            "position": list(piece.center),
            "color": piece.color,
        }
        if isinstance(piece, Box)
        else {"src": f"reference/{piece.name}.stl", "color": piece.color}
        for piece in part.pieces
    ]


def render(model, poses, schema_ref, sliced=None):
    parts = []
    for part in model.parts:
        position, rotation = poses.get(part.id, ([0, 0, 0], [0, 0, 0]))
        item = {
            "id": part.id,
            "label": part.label,
            "kind": "print" if isinstance(part, PrintPart) else "reference",
            "position": list(position),
            "rotation": list(rotation),
            "meshes": _meshes(part),
        }
        if part.drag:
            item["drag"] = {
                "axis": list(part.drag.axis),
                "maxDistance": part.drag.max_distance,
            }
        parts.append(item)
    declared = model.info["printInfo"]
    summary = declared["summary"]
    sections = [
        {"title": "Cấu hình in", "rows": print_rows(model.print_settings), "notes": [], "links": []},
        *declared["sections"],
    ]
    if sliced:
        summary = (
            f"{grams_vn(sliced['grams'])} {model.print_settings.filament} · "
            f"{duration_vn(sliced['seconds'])} · Bambu P1S"
        )
        sections.append(slice_section(model, sliced))
    info = {**model.info, "printInfo": {"summary": summary, "sections": sections}}
    return clean(
        {
            "$schema": schema_ref,
            "schemaVersion": SCHEMA_VERSION,
            "units": "mm",
            **info,
            "id": model.id,
            "parts": parts,
            "measurements": model.measurements,
            "animations": model.animations,
            "downloads": {"bundle": f"{model.id}.zip", "step": "assembly.step"},
            **({"print": sliced} if sliced else {}),
        }
    )
