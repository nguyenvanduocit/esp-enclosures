"""Model declarations and their model.json rendering. No CAD or file I/O here."""

import math
from dataclasses import dataclass
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
    ):
        self.id = id
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


def render(model, poses, schema_ref):
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
    return clean(
        {
            "$schema": schema_ref,
            "schemaVersion": SCHEMA_VERSION,
            "units": "mm",
            **model.info,
            "id": model.id,
            "parts": parts,
            "measurements": model.measurements,
            "animations": model.animations,
            "downloads": {"bundle": f"{model.id}.zip", "step": "assembly.step"},
        }
    )
