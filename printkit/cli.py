"""printkit command line: new, cad, build."""
import argparse
import importlib.util
import os
import sys

from jsonschema import ValidationError

from printkit import bundle
from printkit.catalog import ROOT
from printkit.export import ModelError, export


def load_model(path):
    spec = importlib.util.spec_from_file_location(f'printkit_model_{path.parent.name.replace("-", "_")}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.model


def cad(model_id):
    folder = ROOT / 'models' / model_id
    model = load_model(folder / 'model.py')
    if model.id != model_id:
        raise ModelError(f'{folder / "model.py"} declares id {model.id!r}, expected {model_id!r}')
    _, report = export(model, folder, os.path.relpath(ROOT / 'model.schema.json', folder))
    print(f'{model_id}: {len(report["parts"])} print parts, {len(report["checks"])} checks passed')


def main(argv=None):
    parser = argparse.ArgumentParser(prog='printkit')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('cad', help='build, verify and export one model').add_argument('model')
    commands.add_parser('build', help='validate every model, version viewer assets, package offline ZIPs')
    args = parser.parse_args(argv)
    try:
        if args.command == 'cad':
            cad(args.model)
        elif args.command == 'build':
            bundle.build_all()
    except (ModelError, ValueError, ValidationError) as error:
        print(f'printkit: {error}', file=sys.stderr)
        return 1
    return 0
