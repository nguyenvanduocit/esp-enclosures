"""Slice print parts with Bambu Studio's CLI for a Bambu Lab P1S.

Pure helpers (preset flattening, settings, G-code header) come first; the CLI run follows."""

import re

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
