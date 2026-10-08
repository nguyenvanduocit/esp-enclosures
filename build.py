# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.23.0"]
# ///
"""Validate model data and package the shared app as offline model downloads."""
import base64
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
MODULES = ['viewer/vendor/three.module.min.js', 'viewer/vendor/OrbitControls.js',
           'viewer/resources.js', 'viewer/model-core.js', 'viewer/part-drag.js',
           'viewer/dimensions.js', 'viewer/renderer.js', 'viewer/app.js']


def local_file(folder, value):
    path = (folder / value).resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file():
        raise ValueError(f'Missing or invalid asset: {folder.name}/{value}')
    return path


def unique_ids(items, label):
    ids = [item['id'] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f'Duplicate {label} id')
    return set(ids)


def validate_model(model, folder):
    schema = json.loads((ROOT / 'model.schema.json').read_text())
    Draft202012Validator(schema).validate(model)
    if model['id'] != folder.name:
        raise ValueError('Model id must match its folder name')
    ids = unique_ids(model['parts'], 'part')
    unique_ids(model['measurements'], 'measurement')
    unique_ids(model['animations'], 'animation')
    unique_ids(model['camera']['views'], 'view')
    if model['camera']['minDistance'] >= model['camera']['maxDistance']:
        raise ValueError('Camera distance limits are reversed')
    for path in [model['thumbnail'], model['downloads']['step']]:
        local_file(folder, path)
    for part in model['parts']:
        if part.get('drag') and not math.isclose(math.hypot(*part['drag']['axis']), 1, abs_tol=1e-8):
            raise ValueError('Drag axis must be a unit vector')
        if part['kind'] == 'print' and any('src' not in mesh for mesh in part['meshes']):
            raise ValueError('Print parts require STL assets')
        for mesh in part['meshes']:
            if 'src' in mesh:
                data = local_file(folder, mesh['src']).read_bytes()
                if len(data) < 84 or len(data) != 84 + int.from_bytes(data[80:84], 'little') * 50:
                    raise ValueError(f'Invalid binary STL: {mesh["src"]}')
            elif any(size <= 0 for size in mesh['size']):
                raise ValueError('Primitive sizes must be positive')
    for measure in model['measurements']:
        refs = [measure['followPart'], measure.get('visibleWith', measure['followPart'])]
        refs += [variant['whenHidden'] for variant in measure.get('variants', [])]
        if not set(refs) <= ids:
            raise ValueError('Measurement references an unknown part')
        if any(len(variant['lines']) != len(measure['lines']) for variant in measure.get('variants', [])):
            raise ValueError('Measurement variants must have the same number of lines')
        for line in measure['lines']:
            if line['a'] == line['b']:
                raise ValueError('Measurement line has zero length')
    parts = {part['id']: part for part in model['parts']}
    for animation in model['animations']:
        tracks = animation['tracks']
        targets = [track['part'] for track in tracks]
        if len(targets) != len(set(targets)) or not set(targets) <= ids or not set(animation['openPose']) <= ids:
            raise ValueError('Animation has duplicate or unknown part references')
        if animation['measureReveal'][0] >= animation['measureReveal'][1]:
            raise ValueError('Measurement reveal must have a positive duration')
        for keys in [animation['camera']] + [track['keyframes'] for track in tracks]:
            times = [frame['time'] for frame in keys]
            if times[0] != 0 or times[-1] != 1 or any(a >= b for a, b in zip(times, times[1:])):
                raise ValueError('Keyframes must increase strictly from 0 to 1')
            if keys[0]['value'] != [0, 0, 0] or keys[-1]['value'] != [0, 0, 0]:
                raise ValueError('Animation must begin and end at the installed pose')
        for target, values in [(track['part'], [frame['value'] for frame in track['keyframes']]) for track in tracks] + [(target, [value]) for target, value in animation['openPose'].items()]:
            drag = parts[target].get('drag')
            if not drag:
                continue
            for value in values:
                distance = sum(a * b for a, b in zip(value, drag['axis']))
                residual = [a - distance * b for a, b in zip(value, drag['axis'])]
                if distance < 0 or distance > drag['maxDistance'] or math.hypot(*residual) > 1e-8:
                    raise ValueError('Animation is outside the part removal axis or limits')
    return model


def load_catalog():
    paths = json.loads((ROOT / 'models.json').read_text())
    models = []
    for path in paths:
        manifest = local_file(ROOT, path)
        models.append((manifest, validate_model(json.loads(manifest.read_text()), manifest.parent)))
    unique_ids([model for _, model in models], 'model')
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate model path')
    return models


def offline_html(manifest, model):
    folder = manifest.parent
    assets = {}
    paths = [manifest, local_file(folder, model['thumbnail']), local_file(folder, model['downloads']['step'])]
    paths += [local_file(folder, mesh['src']) for part in model['parts'] for mesh in part['meshes'] if 'src' in mesh]
    for path in paths:
        assets[path.relative_to(ROOT).as_posix()] = base64.b64encode(path.read_bytes()).decode()
    assets['models.json'] = base64.b64encode(json.dumps([manifest.relative_to(ROOT).as_posix()]).encode()).decode()
    modules = [[name, (ROOT / name).read_text()] for name in MODULES]
    # Each dependency appears before its importers; the module code is unchanged.
    boot = 'window.offlineAssets=' + json.dumps(assets, separators=(',', ':')) + ';\n'
    boot += 'const modules=' + json.dumps(modules, separators=(',', ':')) + ';\n'
    boot += '''const urls = new Map();
for (const [path, source] of modules) {
  const code = source.replace(/from (['"])(\\.[^'"]+)\\1/g, (_, quote, specifier) => {
    const dependency = new URL(specifier, 'https://offline/' + path).pathname.slice(1);
    if (!urls.has(dependency)) throw new Error('Missing module: ' + dependency);
    return 'from ' + quote + urls.get(dependency) + quote;
  });
  urls.set(path, URL.createObjectURL(new Blob([code], {type:'text/javascript'})));
}
'''
    boot += f"if (!location.hash) location.hash = '#model/{model['id']}';\n"
    boot += "await import(urls.get('viewer/app.js'));\n"
    boot += "for (const url of urls.values()) URL.revokeObjectURL(url);\n"
    html = (ROOT / 'index.html').read_text()
    html = re.sub(r'<link rel="stylesheet" href="viewer/style.css(?:\?[^"]*)?">', lambda _: '<style>' + (ROOT / 'viewer/style.css').read_text() + '</style>', html)
    html = re.sub(r'<script type="importmap">.*?</script>', '', html, flags=re.S)
    return re.sub(r'<script type="module" src="viewer/app.js(?:\?[^"]*)?"></script>', lambda _: '<script type="module">' + boot.replace('</', '<\\/') + '</script>', html)


def version_assets():
    digest = hashlib.sha256()
    for path in MODULES + ['viewer/style.css']:
        digest.update((ROOT / path).read_bytes())
    version = digest.hexdigest()[:12]
    html = (ROOT / 'index.html').read_text()
    html = re.sub(r'<script type="importmap">.*?</script>\n?', '', html, flags=re.S)
    imports = {'./' + path: './' + path + '?v=' + version for path in MODULES}
    importmap = '<script type="importmap">' + json.dumps({'imports': imports}, separators=(',', ':')) + '</script>\n'
    html = re.sub(r'(<script type="module" src="viewer/app.js)(?:\?[^"]*)?("></script>)', lambda m: importmap + m[1] + '?v=' + version + m[2], html)
    html = re.sub(r'(href="viewer/style.css)(?:\?[^"]*)?(")', lambda m: m[1] + '?v=' + version + m[2], html)
    (ROOT / 'index.html').write_text(html)


def build():
    models = load_catalog()
    version_assets()
    for manifest, model in models:
        folder = manifest.parent
        target = folder / model['downloads']['bundle']
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('index.html', offline_html(manifest, model))
            archive.write(ROOT / 'model.schema.json', 'model.schema.json')
            archive.write(ROOT / 'viewer/vendor/LICENSE', 'THREE-LICENSE.txt')
            for path in sorted(folder.rglob('*')):
                if not path.is_file() or path.suffix in ('.zip', '.pyc') or '__pycache__' in path.parts or path.name == '.DS_Store':
                    continue
                archive.write(path, path.relative_to(ROOT).as_posix())
        print(f'{model["id"]}: validated, packaged {target.stat().st_size:,} bytes')


if __name__ == '__main__':
    build()
