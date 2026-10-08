import copy
import json

import pytest
from jsonschema import ValidationError

from printkit.catalog import load_catalog, validate_model


@pytest.fixture
def battery_model():
    manifest = next(
        path
        for path, model in load_catalog()
        if model["id"] == "esp32-c3-supermini-18650"
    )
    return json.loads(manifest.read_text()), manifest.parent


def test_all_models():
    assert {"esp32-c3-supermini", "esp32-c3-supermini-18650"} <= {
        model["id"] for _, model in load_catalog()
    }


def test_unknown_schema_version(battery_model):
    model, folder = battery_model
    model["schemaVersion"] = 99
    with pytest.raises(ValidationError):
        validate_model(model, folder)


def test_unknown_fields(battery_model):
    model, folder = battery_model
    model["parts"][0]["javascript"] = "alert(1)"
    with pytest.raises(ValidationError):
        validate_model(model, folder)


def test_parent_asset_path(battery_model):
    model, folder = battery_model
    model["parts"][0]["meshes"][0]["src"] = "../another/base.stl"
    with pytest.raises(ValidationError):
        validate_model(model, folder)


def test_duplicate_parts(battery_model):
    model, folder = battery_model
    model["parts"].append(copy.deepcopy(model["parts"][0]))
    with pytest.raises(ValueError, match="Duplicate part"):
        validate_model(model, folder)


def test_missing_asset(battery_model):
    model, folder = battery_model
    model["parts"][0]["meshes"][0]["src"] = "missing.stl"
    with pytest.raises(ValueError, match="Missing or invalid asset"):
        validate_model(model, folder)


def test_dangling_animation(battery_model):
    model, folder = battery_model
    model["animations"][0]["tracks"][0]["part"] = "missing"
    with pytest.raises(ValueError, match="unknown part"):
        validate_model(model, folder)


def test_keyframe_order(battery_model):
    model, folder = battery_model
    model["animations"][0]["tracks"][0]["keyframes"][1]["time"] = 0
    with pytest.raises(ValueError, match="increase strictly"):
        validate_model(model, folder)


def test_drag_limits(battery_model):
    model, folder = battery_model
    model["animations"][0]["openPose"]["usbCap"] = [0, -100, 0]
    with pytest.raises(ValueError, match="removal axis or limits"):
        validate_model(model, folder)


def test_measurement_part(battery_model):
    model, folder = battery_model
    model["measurements"][0]["followPart"] = "missing"
    with pytest.raises(ValueError, match="Measurement references"):
        validate_model(model, folder)


def test_variant_line_count(battery_model):
    model, folder = battery_model
    model["measurements"][0]["variants"][0]["lines"].pop()
    with pytest.raises(ValueError, match="same number"):
        validate_model(model, folder)
