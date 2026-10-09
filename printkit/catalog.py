"""Load models.json and validate every model manifest against the schema and its own references."""

import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "model.schema.json"
# model.json floats carry 6 decimals (manifest.clean), so a unit vector is off by up to √3·5e-7.
ROUNDING = 1e-6


def local_file(folder, value):
    path = (folder / value).resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file():
        raise ValueError(f"Missing or invalid asset: {folder.name}/{value}")
    return path


def unique_ids(items, label):
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate {label} id")
    return set(ids)


def validate_data(model):
    Draft202012Validator(json.loads(SCHEMA.read_text())).validate(model)
    ids = unique_ids(model["parts"], "part")
    unique_ids(model["measurements"], "measurement")
    unique_ids(model["animations"], "animation")
    if model["camera"]["minDistance"] >= model["camera"]["maxDistance"]:
        raise ValueError("Camera distance limits are reversed")
    for part in model["parts"]:
        if part.get("drag") and not math.isclose(
            math.hypot(*part["drag"]["axis"]), 1, abs_tol=ROUNDING
        ):
            raise ValueError("Drag axis must be a unit vector")
        carried = set(part.get("drag", {}).get("carries", ()))
        if part["id"] in carried or not carried <= ids:
            raise ValueError("Drag carries an unknown part or the part itself")
        if part["kind"] == "print" and any(
            "src" not in mesh for mesh in part["meshes"]
        ):
            raise ValueError("Print parts require STL assets")
        for mesh in part["meshes"]:
            if "src" not in mesh and any(size <= 0 for size in mesh["size"]):
                raise ValueError("Primitive sizes must be positive")
    if "print" in model:
        printed = {part["id"] for part in model["parts"] if part["kind"] == "print"}
        if {item["id"] for item in model["print"]["parts"]} - printed:
            raise ValueError("Print stats reference a part that is not printed")
    for measure in model["measurements"]:
        refs = [
            measure["followPart"],
            measure.get("visibleWith", measure["followPart"]),
        ]
        refs += [variant["whenHidden"] for variant in measure.get("variants", [])]
        if not set(refs) <= ids:
            raise ValueError("Measurement references an unknown part")
        if any(
            len(variant["lines"]) != len(measure["lines"])
            for variant in measure.get("variants", [])
        ):
            raise ValueError("Measurement variants must have the same number of lines")
        for line in measure["lines"]:
            if line["a"] == line["b"]:
                raise ValueError("Measurement line has zero length")
    parts = {part["id"]: part for part in model["parts"]}
    for animation in model["animations"]:
        tracks = animation["tracks"]
        targets = [track["part"] for track in tracks]
        if (
            len(targets) != len(set(targets))
            or not set(targets) <= ids
            or not set(animation["openPose"]) <= ids
        ):
            raise ValueError("Animation has duplicate or unknown part references")
        if animation["measureReveal"][0] >= animation["measureReveal"][1]:
            raise ValueError("Measurement reveal must have a positive duration")
        for keys in [animation["camera"]] + [track["keyframes"] for track in tracks]:
            times = [frame["time"] for frame in keys]
            if (
                times[0] != 0
                or times[-1] != 1
                or any(a >= b for a, b in zip(times, times[1:]))
            ):
                raise ValueError("Keyframes must increase strictly from 0 to 1")
            if keys[0]["value"] != [0, 0, 0] or keys[-1]["value"] != [0, 0, 0]:
                raise ValueError("Animation must begin and end at the installed pose")
        poses = [
            (track["part"], [frame["value"] for frame in track["keyframes"]])
            for track in tracks
        ]
        poses += [(target, [value]) for target, value in animation["openPose"].items()]
        for target, values in poses:
            drag = parts[target].get("drag")
            if not drag:
                continue
            for value in values:
                distance = sum(a * b for a, b in zip(value, drag["axis"]))
                residual = [a - distance * b for a, b in zip(value, drag["axis"])]
                if (
                    distance < 0
                    or distance > drag["maxDistance"]
                    or math.hypot(*residual) > ROUNDING * (1 + distance)
                ):
                    raise ValueError(
                        "Animation is outside the part removal axis or limits"
                    )
    return model


def validate_files(model, folder):
    paths = [model["thumbnail"], model["downloads"]["step"]]
    if "print" in model:
        paths += [model["print"]["project"], model["print"]["layers"]]
    for path in paths:
        local_file(folder, path)
    for part in model["parts"]:
        for mesh in part["meshes"]:
            if "src" in mesh:
                data = local_file(folder, mesh["src"]).read_bytes()
                if (
                    len(data) < 84
                    or len(data) != 84 + int.from_bytes(data[80:84], "little") * 50
                ):
                    raise ValueError(f"Invalid binary STL: {mesh['src']}")


def validate_model(model, folder):
    validate_data(model)
    if model["id"] != folder.name:
        raise ValueError("Model id must match its folder name")
    validate_files(model, folder)
    return model


def load_catalog():
    paths = json.loads((ROOT / "models.json").read_text())
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate model path")
    models = []
    for path in paths:
        manifest = local_file(ROOT, path)
        try:
            model = validate_model(json.loads(manifest.read_text()), manifest.parent)
        except ValidationError as error:
            raise ValueError(f"{path}: {error.message}") from error
        except ValueError as error:
            raise ValueError(f"{path}: {error}") from error
        models.append((manifest, model))
    unique_ids([model for _, model in models], "model")
    return models
