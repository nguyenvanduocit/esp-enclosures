import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import ROOT, load_catalog, validate_model
from jsonschema import ValidationError


class ModelValidation(unittest.TestCase):
    def setUp(self):
        self.folder = ROOT / 'esp32-c3-supermini-18650'
        self.model = json.loads((self.folder / 'model.json').read_text())

    def test_all_models(self):
        self.assertTrue({"esp32-c3-supermini", "esp32-c3-supermini-18650"} <= {model["id"] for _, model in load_catalog()})

    def test_unknown_schema_version(self):
        self.model['schemaVersion'] = 99
        with self.assertRaises(ValidationError):
            validate_model(self.model, self.folder)

    def test_unknown_fields(self):
        self.model['parts'][0]['javascript'] = 'alert(1)'
        with self.assertRaises(ValidationError):
            validate_model(self.model, self.folder)

    def test_parent_asset_path(self):
        self.model['parts'][0]['meshes'][0]['src'] = '../another/base.stl'
        with self.assertRaises(ValidationError):
            validate_model(self.model, self.folder)

    def test_duplicate_parts(self):
        self.model['parts'].append(copy.deepcopy(self.model['parts'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate part'):
            validate_model(self.model, self.folder)

    def test_missing_asset(self):
        self.model['parts'][0]['meshes'][0]['src'] = 'missing.stl'
        with self.assertRaisesRegex(ValueError, 'Missing or invalid asset'):
            validate_model(self.model, self.folder)

    def test_dangling_animation(self):
        self.model['animations'][0]['tracks'][0]['part'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'unknown part'):
            validate_model(self.model, self.folder)

    def test_keyframe_order(self):
        self.model['animations'][0]['tracks'][0]['keyframes'][1]['time'] = 0
        with self.assertRaisesRegex(ValueError, 'increase strictly'):
            validate_model(self.model, self.folder)

    def test_drag_limits(self):
        self.model['animations'][0]['openPose']['usbCap'] = [0, -100, 0]
        with self.assertRaisesRegex(ValueError, 'removal axis or limits'):
            validate_model(self.model, self.folder)

    def test_measurement_part(self):
        self.model['measurements'][0]['followPart'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'Measurement references'):
            validate_model(self.model, self.folder)

    def test_variant_line_count(self):
        self.model['measurements'][0]['variants'][0]['lines'].pop()
        with self.assertRaisesRegex(ValueError, 'same number'):
            validate_model(self.model, self.folder)


if __name__ == '__main__':
    unittest.main()
