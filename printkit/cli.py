"""printkit command line: new, cad, slice, build."""
import argparse
import importlib.util
import json
import os
import re
import shutil
import struct
import sys
import zlib

from jsonschema import ValidationError

from printkit import bundle
from printkit.catalog import ROOT
from printkit.export import ModelError, export
from printkit.slicer import SliceError, slice_model

ID_PATTERN = re.compile(r'[a-z][a-z0-9-]*')
TEMPLATE = '''"""{id}: describe the object here. Millimetres, Z up."""
from printkit import Drag, Model, pulse
from printkit.shapes import block

W, L, H = 40.0, 30.0, 10.0

model = Model(
    '{id}', title='{id}', description='Mô tả ngắn.', category='Khác', status='Bản nháp',
    thumbnail='thumbnail.png', dimensions=(W, L, H),
    camera={{'position': [80, -110, 90], 'target': [0, 0, H / 2], 'minDistance': 30, 'maxDistance': 400,
            'views': [{{'id': 'top', 'label': 'Trên', 'offset': [0, -0.01, 200]}}]}},
    grid={{'size': 100, 'divisions': 20}},
    print_info={{'summary': 'Chưa in thử', 'sections': []}})


@model.part('body', 'Thân', color='#367c85', drag=Drag((0, 0, 1), 30))
def body():
    return block(W, L, H)


model.animation('lift', 'Nhấc lên', duration=6, open_pose={{'body': (0, 0, 20)}},
                tracks={{'body': pulse((0, 0, 20))}}, camera=pulse((0, 0, 0)), measure_reveal=(0.34, 0.64))
'''


def placeholder_png():
    """1×1 grey PNG so a new model passes asset validation before a real thumbnail exists."""
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    header = struct.pack('>IIBBBBB', 1, 1, 8, 0, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(b'\x00\x80')) + chunk(b'IEND', b'')


def scaffold(model_id):
    if not ID_PATTERN.fullmatch(model_id):
        raise ValueError(f'invalid model id {model_id!r}: use lowercase letters, digits and hyphens')
    folder = ROOT / 'models' / model_id
    if folder.exists():
        raise ValueError(f'{folder} already exists')
    folder.mkdir(parents=True)
    (folder / 'model.py').write_text(TEMPLATE.format(id=model_id))
    (folder / 'README.md').write_text(f'# {model_id}\n\nMở model trong [app chung](../../#model/{model_id}).\n')
    (folder / 'thumbnail.png').write_bytes(placeholder_png())
    try:
        cad(model_id)
    except Exception:
        shutil.rmtree(folder)
        raise
    catalog = ROOT / 'models.json'
    paths = json.loads(catalog.read_text())
    catalog.write_text(json.dumps(paths + [f'models/{model_id}/model.json'], indent=2) + '\n')
    print(f'{model_id}: scaffolded and built; edit models/{model_id}/model.py, then run `uv run printkit cad {model_id}`')


def load_model(path):
    spec = importlib.util.spec_from_file_location(f'printkit_model_{path.parent.name.replace("-", "_")}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.model


def cad(model_id, slicer=None):
    folder = ROOT / 'models' / model_id
    if not (folder / 'model.py').is_file():
        raise ModelError(f'{folder / "model.py"} not found; create it with `printkit new {model_id}`')
    model = load_model(folder / 'model.py')
    if model.id != model_id:
        raise ModelError(f'{folder / "model.py"} declares id {model.id!r}, expected {model_id!r}')
    _, report = export(model, folder, os.path.relpath(ROOT / 'model.schema.json', folder), slicer=slicer)
    print(f'{model_id}: {len(report["parts"])} print parts, {len(report["checks"])} checks passed')
    if report.get('print'):
        result = report['print']
        print(f"{model_id}: sliced {result['layerCount']} layers · {result['grams']} g · "
              f"{round(result['seconds'] / 60)} min ({result['slicer']})")
    for warning in report['warnings']:
        print(f'warning: {warning}', file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='printkit')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('new', help='scaffold a model folder and add it to models.json').add_argument('model')
    commands.add_parser('cad', help='build, verify and export one model').add_argument('model')
    commands.add_parser('slice', help='build, verify and slice one model with Bambu Studio').add_argument('model')
    commands.add_parser('build', help='validate every model, version viewer assets, package offline ZIPs')
    args = parser.parse_args(argv)
    try:
        if args.command == 'new':
            scaffold(args.model)
        elif args.command == 'cad':
            cad(args.model)
        elif args.command == 'slice':
            cad(args.model, slicer=slice_model)
        elif args.command == 'build':
            bundle.build_all()
    except (ModelError, SliceError, ValueError, ValidationError) as error:
        print(f'printkit: {error}', file=sys.stderr)
        return 1
    return 0
