import pytest

from printkit.manifest import Print
from printkit.slicer import (
    SliceError,
    apply_overrides,
    flatten,
    ignored_settings,
    parse_duration,
    parse_summary,
    process_settings,
)

INDEX = {
    "leaf": {
        "name": "leaf",
        "inherits": "mid",
        "wall_loops": "3",
        "instantiation": "true",
    },
    "mid": {
        "name": "mid",
        "inherits": "root",
        "layer_height": "0.16",
        "wall_loops": "2",
    },
    "root": {
        "name": "root",
        "layer_height": "0.2",
        "bridge_speed": ["50", "50"],
        "from": "system",
    },
}

HEADER = """; HEADER_BLOCK_START
; BambuStudio 02.08.02.61
; model printing time: 1h 4m 21s; total estimated time: 1h 4m 41s
; total layer number: 158
; total filament length [mm] : 15000.00
; total filament weight [g] : 46.08
; HEADER_BLOCK_END
G1 X1 Y1
"""


def test_flatten_merges_parent_first():
    merged = flatten(INDEX, "leaf")
    assert merged["layer_height"] == "0.16" and merged["wall_loops"] == "3"
    assert merged["bridge_speed"] == ["50", "50"] and merged["from"] == "system"
    assert "inherits" not in merged and "instantiation" not in merged


def test_flatten_unknown_preset():
    with pytest.raises(SliceError, match="missing"):
        flatten(INDEX, "missing")


def test_process_settings_defaults_and_brim():
    assert process_settings(Print()) == {
        "layer_height": "0.16",
        "initial_layer_print_height": "0.2",
        "wall_loops": "2",
        "sparse_infill_density": "15%",
        "sparse_infill_pattern": "grid",
        "enable_support": "0",
        "brim_type": "auto_brim",
    }
    assert process_settings(Print(brim=0))["brim_type"] == "no_brim"
    custom = process_settings(
        Print(brim=4, supports=True, extra={"outer_wall_speed": 60})
    )
    assert custom["brim_type"] == "outer_only" and custom["brim_width"] == "4"
    assert custom["enable_support"] == "1" and custom["outer_wall_speed"] == "60"


def test_apply_overrides_keeps_list_shape():
    process = flatten(INDEX, "leaf")
    result = apply_overrides(
        process, {"bridge_speed": "25", "layer_height": "0.12", "brim_type": "no_brim"}
    )
    assert result["bridge_speed"] == ["25", "25"] and result["layer_height"] == "0.12"
    assert result["brim_type"] == "no_brim" and process["bridge_speed"] == ["50", "50"]


def test_ignored_settings_reports_mismatch():
    project = {"layer_height": "0.2", "bridge_speed": ["25", "25"], "wall_loops": "3"}
    problems = ignored_settings(
        project,
        {
            "layer_height": "0.16",
            "bridge_speed": "25",
            "wall_loops": "3",
            "typo_key": "1",
        },
    )
    assert len(problems) == 2
    assert problems[0].startswith("layer_height") and problems[1].startswith("typo_key")


def test_parse_duration():
    assert parse_duration("1h 4m 41s") == 3881
    assert parse_duration("16m 50s") == 1010
    assert parse_duration("2d 1h") == 176400
    with pytest.raises(SliceError):
        parse_duration("soon")


def test_parse_summary():
    assert parse_summary(HEADER) == {"seconds": 3881, "grams": 46.08, "layerCount": 158}
    with pytest.raises(SliceError, match="weight"):
        parse_summary(HEADER.replace("46.08", "0.00"))
    with pytest.raises(SliceError, match="header"):
        parse_summary("G1 X1\n")
