"""Build a declared model, verify it, and replace its generated files atomically."""
import json
import os
import shutil
import tempfile
from pathlib import Path

import cadquery as cq
import trimesh

from printkit.catalog import validate_data
from printkit.checks import CheckFailed
from printkit.manifest import PrintPart, Solid, render
from printkit.pose import installed_pose
from printkit.printability import assess
from printkit.shapes import rotated

GENERATED = ('*.stl', '*.step', 'model.json', 'verification.json')
PRINT_TOLERANCE = {'tolerance': 0.03, 'angularTolerance': 0.1}
REFERENCE_TOLERANCE = {'tolerance': 0.04, 'angularTolerance': 0.15}


class ModelError(Exception):
    pass


def single_solid(name, shape):
    if not shape.val().isValid() or len(shape.solids().vals()) != 1:
        raise ModelError(f'{name}: BRep must be one valid solid')
    return shape


def printable_mesh(name, shape, path):
    cq.exporters.export(shape, str(path), **PRINT_TOLERANCE)
    mesh = trimesh.load_mesh(path)
    if not (mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0 and len(mesh.split()) == 1):
        raise ModelError(f'{name}: mesh must be one watertight, consistently wound body')
    return mesh


def run_checks(model):
    results, failures = {}, []
    for name, check in model.checks:
        try:
            results[name] = check() or True
        except CheckFailed as error:
            failures.append(f'{name}: {error}')
        except Exception as error:
            failures.append(f'{name}: {type(error).__name__}: {error}')
    if failures:
        raise ModelError('Checks failed:\n' + '\n'.join(failures))
    return results


def rgb(hex_color):
    return cq.Color(*(int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)))


def write_outputs(model, out):
    installed, poses, parts, printability = {}, {}, {}, {}
    for part in model.parts:
        if isinstance(part, PrintPart):
            shape = single_solid(part.id, part.build())
            installed[part.id] = shape
            path = out / f'{part.id}.stl'
            mesh = printable_mesh(part.id, rotated(shape, part.print_rotation), path)
            low, high = mesh.bounds
            translation = [-(low[0] + high[0]) / 2, -(low[1] + high[1]) / 2, -low[2]]
            mesh.apply_translation(translation)
            mesh.export(path)
            printability[part.id] = assess(mesh)
            limit = part.max_overhang_mm2
            if limit is not None and printability[part.id]['overhang_mm2'] > limit:
                raise ModelError(f"{part.id}: overhang {printability[part.id]['overhang_mm2']} mm² exceeds {limit} mm²")
            poses[part.id] = installed_pose(part.print_rotation, translation)
            parts[part.id] = {'watertight': True, 'solid_count': 1, 'volume_mm3': round(float(mesh.volume), 2),
                              'bounds_mm': mesh.bounds.round(3).tolist()}
        else:
            for piece in part.pieces:
                if isinstance(piece, Solid):
                    (out / 'reference').mkdir(exist_ok=True)
                    cq.exporters.export(piece.shape, str(out / 'reference' / f'{piece.name}.stl'), **REFERENCE_TOLERANCE)
    return installed, poses, parts, printability


def write_assembly(model, installed, out):
    assembly = cq.Assembly(name=model.id)
    for part in model.parts:
        if part.id in installed:
            assembly.add(installed[part.id], name=part.id, color=rgb(part.color))
    path = out / 'assembly.step'
    assembly.export(str(path))
    solids = cq.importers.importStep(str(path)).solids().vals()
    if len(solids) != len(installed) or not all(solid.isValid() for solid in solids):
        raise ModelError(f'assembly.step: expected {len(installed)} valid solids, found {len(solids)}')


def replace_generated(folder, out):
    """Swap `out` into `folder` file by file (os.replace; `out` shares the folder's filesystem),
    then delete generated files the new set no longer contains."""
    folder.mkdir(parents=True, exist_ok=True)
    fresh = {path.name for path in out.iterdir()}
    for path in out.iterdir():
        if path.is_dir():
            shutil.rmtree(folder / path.name, ignore_errors=True)
        os.replace(path, folder / path.name)
    for pattern in GENERATED:
        for path in folder.glob(pattern):
            if path.name not in fresh:
                path.unlink()
    if 'reference' not in fresh:
        shutil.rmtree(folder / 'reference', ignore_errors=True)


def export(model, folder, schema_ref):
    """Write all generated files for `model` into `folder`.

    Build, check and validation steps run in a scratch directory beside `folder`; if any of them
    fails, `folder` is left untouched (and is not created). Only after all pass does the replace
    step swap the new files in one by one."""
    folder = Path(folder)
    folder.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder.parent) as scratch:
        out = Path(scratch)
        installed, poses, parts, printability = write_outputs(model, out)
        warnings = [f'{part}: {result["warning"]}' for part, result in printability.items() if 'warning' in result]
        report = {'units': 'mm', 'dimensions': model.info['dimensions'], 'parts': parts,
                  'checks': run_checks(model), 'printability': printability, 'warnings': warnings}
        write_assembly(model, installed, out)
        manifest = validate_data(render(model, poses, schema_ref))
        (out / 'model.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
        (out / 'verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        replace_generated(folder, out)
    return manifest, report
