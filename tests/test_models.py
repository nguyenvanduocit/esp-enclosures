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


class AssetVersions(unittest.TestCase):
    def test_transitive_changes_update_import_map_and_entry_together(self):
        import re
        import tempfile
        from unittest.mock import patch
        from build import version_assets

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'viewer').mkdir()
            (root / 'viewer/app.js').write_text("import './dependency.js';")
            dependency = root / 'viewer/dependency.js'
            dependency.write_text('export const value = 1;')
            (root / 'viewer/style.css').write_text('body {}')
            index = root / 'index.html'
            index.write_text('<link rel="stylesheet" href="viewer/style.css"><script type="module" src="viewer/app.js"></script>')
            with patch('build.ROOT', root), patch('build.MODULES', ['viewer/dependency.js', 'viewer/app.js']):
                version_assets()
                first = index.read_text()
                version_assets()
                self.assertEqual(first, index.read_text())
                dependency.write_text('export const value = 2;')
                version_assets()
            updated = index.read_text()
            self.assertNotEqual(first, updated)
            versions = re.findall(r'\?v=([a-f0-9]+)', updated)
            self.assertEqual(len(versions), 4)
            self.assertEqual(len(set(versions)), 1)
            self.assertEqual(updated.count('type="importmap"'), 1)

    def test_offline_export_embeds_versioned_entry_and_styles(self):
        from build import offline_html
        manifest, model = load_catalog()[0]
        html = offline_html(manifest, model)
        self.assertNotIn('type="importmap"', html)
        self.assertNotIn('src="viewer/app.js', html)
        self.assertNotIn('href="viewer/style.css', html)
        self.assertIn('window.offlineAssets=', html)


if __name__ == '__main__':
    unittest.main()
