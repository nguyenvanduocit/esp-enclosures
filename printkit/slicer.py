"""Slice print parts with Bambu Studio's CLI for a Bambu Lab P1S.

Pure helpers (preset flattening, settings, G-code header) come first; the CLI run follows."""

import json
import plistlib
import re
import subprocess
import tempfile
import zipfile
from functools import cache
from pathlib import Path

from printkit.gcode import parse_layers
from printkit.manifest import PrintPart

MACHINE = "Bambu Lab P1S 0.4 nozzle"
# Bambu ships no P1S-named process preset; this X1C one lists the P1S 0.4 nozzle as compatible.
PROCESS = "0.16mm Optimal @BBL X1C"
FILAMENTS = {"PLA": "Bambu PLA Basic @BBL P1S 0.4 nozzle"}
UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


class SliceError(Exception):
    pass


def flatten(index, name):
    """Merge a preset with its `inherits` chain, parent first. The CLI does not resolve the chain
    itself (it silently falls back to defaults), and rejects presets not marked as system presets."""
    chain, current = [], name
    while current:
        if current not in index:
            raise SliceError(f"Bambu Studio preset {current!r} not found")
        chain.append(index[current])
        current = index[current].get("inherits")
    merged = {}
    for preset in reversed(chain):
        merged.update(preset)
    merged.pop("inherits", None)
    merged.pop("instantiation", None)
    merged["from"] = "system"
    return merged


def setting_text(value):
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def process_settings(settings):
    """Bambu Studio process keys for a Print declaration, as the strings Studio stores."""
    density, pattern = settings.infill
    keys = {
        "layer_height": settings.layer,
        "initial_layer_print_height": settings.first_layer,
        "wall_loops": settings.walls,
        "sparse_infill_density": f"{setting_text(float(density))}%",
        "sparse_infill_pattern": pattern,
        "enable_support": settings.supports,
    }
    if settings.brim == "auto":
        keys["brim_type"] = "auto_brim"
    elif settings.brim:
        keys.update(brim_type="outer_only", brim_width=settings.brim)
    else:
        keys["brim_type"] = "no_brim"
    keys.update(settings.extra)
    return {key: setting_text(value) for key, value in keys.items()}


def apply_overrides(process, overrides):
    """Copy of `process` with overrides; list-valued keys (one entry per extruder) get every entry."""
    result = dict(process)
    for key, text in overrides.items():
        current = process.get(key)
        result[key] = [text] * len(current) if isinstance(current, list) else text
    return result


def ignored_settings(project, overrides):
    """Requested settings that the sliced project's settings do not show."""
    problems = []
    for key, text in overrides.items():
        actual = project.get(key)
        values = actual if isinstance(actual, list) else [actual]
        if not values or any(value != text for value in values):
            problems.append(f"{key}: requested {text!r}, Studio used {actual!r}")
    return problems


def parse_duration(text):
    matches = re.findall(r"(\d+)([dhms])", text)
    if not matches:
        raise SliceError(f"unreadable duration {text!r}")
    return sum(int(amount) * UNITS[unit] for amount, unit in matches)


def parse_summary(gcode):
    header = gcode.split("; HEADER_BLOCK_END", 1)[0]
    time = re.search(r"total estimated time: ([^;\n]+)", header)
    grams = re.search(r"total filament weight \[g\] : ([\d.]+)", header)
    layers = re.search(r"total layer number: (\d+)", header)
    if not (time and grams and layers):
        raise SliceError(
            "G-code header lacks estimated time, filament weight or layer count"
        )
    if float(grams[1]) <= 0:
        raise SliceError(
            "G-code reports 0 g filament weight; the filament preset was not applied"
        )
    return {
        "seconds": parse_duration(time[1]),
        "grams": float(grams[1]),
        "layerCount": int(layers[1]),
    }


STUDIO = Path("/Applications/BambuStudio.app")
BINARY = STUDIO / "Contents/MacOS/BambuStudio"
PROFILES = STUDIO / "Contents/Resources/profiles/BBL"
TIMEOUT_S = 600


def studio_version():
    return plistlib.loads((STUDIO / "Contents/Info.plist").read_bytes())[
        "CFBundleShortVersionString"
    ]


@cache
def load_index(kind):
    """Bundled presets of one kind by name. Files Studio itself cannot parse are skipped."""
    index = {}
    for path in sorted((PROFILES / kind).glob("*.json")):
        try:
            preset = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if "name" in preset:
            index[preset["name"]] = preset
    return index


def write_presets(settings, folder):
    if settings.filament not in FILAMENTS:
        raise SliceError(
            f"filament {settings.filament!r} not supported; use one of {sorted(FILAMENTS)}"
        )
    overrides = process_settings(settings)
    presets = {
        "machine": flatten(load_index("machine"), MACHINE),
        "process": apply_overrides(flatten(load_index("process"), PROCESS), overrides),
        "filament": flatten(load_index("filament"), FILAMENTS[settings.filament]),
    }
    for kind, preset in presets.items():
        (folder / f"{kind}.json").write_text(json.dumps(preset, indent=1))
    return overrides


def run_studio(stls, presets, target, work):
    """Slice `stls` on one auto-arranged plate. Studio writes result.json into its cwd on failure,
    so it always runs inside `work`."""
    command = [
        str(BINARY),
        "--load-settings",
        f"{presets / 'machine.json'};{presets / 'process.json'}",
        "--load-filaments",
        str(presets / "filament.json"),
        "--arrange",
        "1",
        "--slice",
        "0",
        "--export-3mf",
        str(target),
        *map(str, stls),
    ]
    try:
        result = subprocess.run(
            command, cwd=work, capture_output=True, text=True, timeout=TIMEOUT_S
        )
    except subprocess.TimeoutExpired:
        raise SliceError(f"Bambu Studio did not finish within {TIMEOUT_S} s") from None
    if result.returncode != 0:
        raise SliceError(
            f"Bambu Studio exited {result.returncode}: {failure_message(work, result)}"
        )
    try:
        with zipfile.ZipFile(target) as project:
            return (
                project.read("Metadata/plate_1.gcode").decode(),
                json.loads(project.read("Metadata/project_settings.config")),
            )
    except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        raise SliceError(
            f"Bambu Studio produced no readable project: {error!r}"
        ) from None


def failure_message(work, result):
    """Studio's own error_string from result.json, else the tail of stderr."""
    try:
        message = json.loads((work / "result.json").read_text()).get("error_string")
    except (OSError, ValueError, AttributeError):
        message = None
    return message or result.stderr.strip()[-500:]


def slice_plate(stls, settings, target, work):
    presets = work / "presets"
    presets.mkdir(exist_ok=True)
    overrides = write_presets(settings, presets)
    gcode, project = run_studio(stls, presets, target, work)
    problems = ignored_settings(project, overrides)
    if problems:
        raise SliceError("Bambu Studio ignored settings: " + "; ".join(problems))
    return gcode, parse_summary(gcode)


def slice_model(model, out):
    """Slice every print STL in `out` on one P1S plate, then each part alone for per-part numbers.

    Writes out/print/<id>.gcode.3mf and out/print/layers.json; returns the model.json `print` block."""
    if not BINARY.exists():
        raise SliceError(
            f"{BINARY} not found; install it with `brew install --cask bambu-studio`"
        )
    parts = [part for part in model.parts if isinstance(part, PrintPart)]
    folder = out / "print"
    folder.mkdir()
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)
        gcode, plate = slice_plate(
            [out / f"{part.id}.stl" for part in parts],
            model.print_settings,
            folder / f"{model.id}.gcode.3mf",
            work,
        )
        (folder / "layers.json").write_text(
            json.dumps(parse_layers(gcode), separators=(",", ":"))
        )
        per_part = []
        for part in parts:
            _, summary = slice_plate(
                [out / f"{part.id}.stl"],
                model.print_settings,
                work / f"{part.id}.gcode.3mf",
                work,
            )
            per_part.append(
                {"id": part.id, "seconds": summary["seconds"], "grams": summary["grams"]}
            )
    return {
        "project": f"print/{model.id}.gcode.3mf",
        "layers": "print/layers.json",
        "slicer": f"Bambu Studio {studio_version()}",
        **plate,
        "parts": per_part,
    }
