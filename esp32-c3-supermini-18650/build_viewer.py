"""Embed pinned Three.js/OrbitControls and CAD meshes into a portable offline viewer."""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def encode(path):
    return base64.b64encode(path.read_bytes()).decode()

# The two MIT-licensed libraries are vendored alongside the viewer template.
assets = {key: encode(ROOT / 'vendor' / filename) for key, filename in
          [('three', 'three.module.min.js'), ('orbit', 'OrbitControls.js')]}
assets.update({name: encode(ROOT / f'{name}.stl') for name in
               ['base', 'battery_lid', 'electronics_lid', 'usb_cap']})
assets['usb_cap_origin'] = json.loads((ROOT / 'verification.json').read_text())['usb_cap']['installed_origin']
assets['reference'] = json.loads((ROOT / 'reference.json').read_text())
html = (ROOT / 'viewer-template.html').read_text().replace('__ASSETS__', json.dumps(assets,separators=(',',':')))
html = html.replace('<head>', '<head><!-- Three.js / OrbitControls 0.169.0\n' + (ROOT / 'vendor' / 'LICENSE').read_text() + '-->', 1)
(ROOT / 'viewer.html').write_text(html)
print(f'Built viewer.html: {len(html.encode()):,} bytes')
