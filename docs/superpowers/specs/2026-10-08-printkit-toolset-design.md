# printkit: a toolset for designing, checking, slicing and previewing 3D prints

Date: 2026-10-08 · Status: awaiting review

## Goal

Turn this repository into a reusable toolset for **any 3D-printed model**: write one
`model.py`, and the toolset produces printable STL/STEP, verification, the interactive
viewer manifest, a sliced Bambu P1S project, and an in-browser print simulation.

Success criteria:

1. A new model is one folder with `model.py` + `README.md`; no copied helpers, no
   hand-written coordinates outside `model.py`.
2. Changing a dimension constant in `model.py` updates STL, STEP, viewer poses,
   measurement lines and labels, and print statistics.
3. Both existing models keep the same installed geometry (see P1 acceptance).
4. Print orientation problems are reported at CAD time; real slicing uses Bambu Studio.
5. Anyone opening the Pages app can scrub through the sliced print layer by layer.

## Decisions

| Topic | Decision |
|---|---|
| Model scope | Any 3D print. Core is domain-neutral; domain parts live in `printkit/library/`. |
| Repo layout | One repo. Toolset at the root, models under `models/<id>/`. |
| Naming | Python package `printkit`. Repo rename is done later by the owner on GitHub; code references to `esp-enclosures` (`index.html` GitHub link, README, repo description) are updated in the same change. |
| Source of truth | `model.py` declares everything. `model.json` is a generated, committed file. |
| Part modelling | Every part is modelled in its installed pose. The toolkit derives print orientation, STL, and viewer pose. |
| Slicer | Bambu Studio CLI, pinned to Homebrew cask `bambu-studio` 02.08.02.61. No hand-written Bambu 3MF metadata. |
| Printer | Bambu Lab P1S, 0.4 mm nozzle. |
| Plates | One plate per model: all print parts sliced together. |
| Print simulation | Precomputed `layers.json` rendered in the existing Three.js viewer. |

## Layout

```text
pyproject.toml              uv project; deps cadquery==2.8.0, trimesh==5.1.1, jsonschema==4.23.0; script `printkit`
printkit/
  shapes.py                 block, rounded, slot and other CadQuery helpers
  checks.py                 overlap, clear, sweep → named check results
  printability.py           overhang, bridges, orientation ranking (pure, trimesh)
  manifest.py               Model, Drag, Print, Box, dim → model.json dict
  export.py                 STL + STEP + reference meshes + verification.json + model.json
  slicer.py                 Bambu Studio CLI invocation, stats, G-code → layers
  library/electronics.py    ESP32-C3 SuperMini board, header pins, 18650 cell
  catalog.py                read models.json, schema + reference validation
  bundle.py                 offline ZIP + asset versioning
  cli.py                    printkit new | cad | slice | build
printers/bambu-p1s-0.4/     machine.json, process.json, filament.json (exported, flattened) + README
models/<id>/
  model.py, README.md, thumbnail.png
  generated: *.stl, enclosure.step, reference/, model.json, verification.json,
             print/<id>.gcode.3mf, print/slice.json, print/<id>.layers.json, <id>.zip
models.json                 list of model.json paths, read by the viewer
model.schema.json           Python ↔ viewer contract, schemaVersion 1
index.html, viewer/         web app; adds viewer/print-preview.js
tests/                      pytest (printkit) + node --test (viewer)
```

`build.py` is removed; its validation moves to `catalog.py` and packaging to `bundle.py`.
`drag-verification.json` and `viewer-verification.json` are removed: they record browser
checks of the per-model viewer (`build_viewer.py`, `viewer-template.html`, commits
`340e47c`, `660c0fa`) that commit `647a7b3` replaced with the shared viewer.

## Commands

| Command | Needs | Does |
|---|---|---|
| `uv run printkit new <id>` | — | Scaffold `models/<id>/model.py` + README, append to `models.json` |
| `uv run printkit cad <id>` | CadQuery | Build parts, run checks, write STL/STEP/reference/model.json/verification.json |
| `uv run printkit slice <id>` | Bambu Studio | Slice all print parts on one plate, write `print/*` and print stats |
| `uv run printkit build` | — | Validate every model, version viewer assets, package offline ZIPs |

Each command reads only the outputs of the previous one, so each can be rerun alone.
`build` does not require `slice` output; the viewer shows "chưa slice" when it is absent.

## Model API

```python
from printkit import Model, Drag, Print, dim
from printkit.checks import clear, sweep
from printkit.library.electronics import esp32_c3_supermini

model = Model("esp32-c3-supermini-18650", title="…", category="Hộp điện tử",
              status="Chưa in thử", thumbnail="thumbnail.png",
              print=Print(layer=0.16, first_layer=0.20, walls=3, infill=(15, "gyroid"),
                          supports=False, filament="PLA"))

@model.part("batteryLid", "Nắp pin", drag=Drag((0, 0, 1), 100), print_rotation=(0, 180, 0))
def battery_lid():
    return installed_lid("battery_lid")          # CadQuery solid in installed pose

model.reference("board", "ESP32", esp32_c3_supermini(at=(ESP_X, ESP_Y, ESP_Z)),
                drag=Drag((0, 0, 1), 90))

model.measure("case", "Vỏ hộp", follow="base", lines=[
    dim((-W/2, -L/2, 0), (W/2, -L/2, 0), offset=(0, -8, 0), name="Rộng"),
])

model.animation("explode", "Mở hộp", duration=10, tracks={...})

@model.check("Battery removal clear")
def battery_removal():
    clear(cell_sweep(), base=base(), holder=HOLDER)   # part builders are cached; obstacles are named
```

Rules:

- `print_rotation` is an Euler XYZ rotation in degrees applied to the installed solid.
  The toolkit then translates it so its minimum Z is 0 and its XY bounding-box centre is
  the origin. The STL is written in that frame; the viewer pose (`position`, `rotation`)
  is the inverse transform, matching `viewer/renderer.js:55-56`.
- `dim(anchor_a, anchor_b, offset, name)` produces `anchorA = anchor_a`,
  `anchorB = anchor_b`, `a = anchor_a + offset`, `b = anchor_b + offset`, and the label
  `f"{|anchor_b - anchor_a|:g} mm · {name}"`. `labelOffset` and
  `variants` are optional arguments.
- Reference components are lists of `Box(size, position, color)` or `(name, solid, color)`.
  `Box` becomes a viewer `box` primitive; solids become STL under `reference/`.
- Animation keyframes stay explicit. Helpers are added only once a pattern repeats in
  three or more models.
- `@model.part` functions run once (cached); checks call them directly. A check raises
  `CheckFailed` or returns a dict of measured values recorded in `verification.json`.
- Generated names: `<part id>.stl`, `reference/<piece>.stl`, `assembly.step`,
  `model.json`, `verification.json`, `<id>.zip`.
- `Print` is model-level; a part may override `supports`. Settings are both slicer input
  and the source of the `printInfo` rows shown in the viewer. Free-text notes stay in
  `model.py`. `Print` arrives with P3; until then `print_info` is a literal in `model.py`.
- `model.py` contains only model-specific geometry, declarations and checks.

## `printkit cad` pipeline

1. Build every part; fail unless the BRep is valid and a single solid.
2. Apply the print transform, export STL (tolerance 0.03 / angular 0.1 for print parts,
   0.04 / 0.15 for references), fail unless the mesh is watertight, winding-consistent,
   positive-volume and one body.
3. Run every `@model.check`; any failure stops the run before files are written, naming
   the check and the parts.
4. Run printability analysis (P2) on each print part.
5. Export the installed assembly as `enclosure.step`, re-import it and confirm the solid
   count and validity.
6. Write `model.json`, `verification.json`.

## P2: printability

Input: a print-oriented trimesh. Pure functions, no I/O.

- Overhang: total area of faces with `normal_z < -cos(45°)` whose centroid is above
  `z = 0.01 mm`. Threshold is a parameter.
- Bridges: connected regions of downward horizontal faces above the bed; report each
  region's Z, both XY extents and area. A single "span" is not reported: for a door in a
  thin wall the bridge runs along the longer extent, under a wide ceiling along the shorter.
- Orientation ranking: the six axis-aligned orientations, ranked by overhang area, then
  bed contact area (descending), then height. If a different orientation ranks first,
  emit a warning; a part with `max_overhang_mm2` fails when exceeded.
- Output: `verification.json → printability.<part>`.

## P3: slicing

- `printers/bambu-p1s-0.4/` holds presets exported from Bambu Studio 02.08.02.61, so they
  are already flattened (no `inherits`). The README records the export steps and version.
- `Print` maps to process keys through one table in `slicer.py`: `layer → layer_height`,
  `first_layer → initial_layer_print_height`, `walls → wall_loops`,
  `infill → sparse_infill_density / sparse_infill_pattern`, `supports → enable_support`,
  `brim → brim_type / brim_width`. Merged presets are written to a temp directory.
- Invocation: `BambuStudio --load-settings "machine.json;process.json"
  --load-filaments filament.json --arrange 1 --slice 0 --export-3mf <out>` with all print
  STLs of the model on one plate.
- Outputs: `print/<id>.gcode.3mf` (sendable to the printer, listed in downloads),
  `print/slice.json` (`time_s`, `filament_g`, `layers`, per-object grams when the G-code
  provides them), `print/<id>.layers.json`.
- `printInfo` time/weight/support rows are generated from `slice.json`.
- Missing Bambu Studio: fail with the install command `brew install --cask bambu-studio`.

**First task of P3 is a spike**: install Bambu Studio, export presets, slice one STL via
the CLI. Verify the CLI accepts the exported presets, the mapped key names exist, and the
G-code header exposes time and weight. If any of these fail, stop and report before
building on it.

## P4: print simulation in the viewer

- `model.json` gains optional `print: {project, layers, stats}`. Additive, so
  `schemaVersion` stays 1.
- `viewer/print-preview.js` adds an "In" mode: the 256 × 256 mm P1S bed, toolpaths at
  their sliced positions, a layer slider (1…N), a Play button that adds one layer per tick,
  the current layer bright and earlier layers dimmed, feature-type colours (outer wall,
  inner wall, infill, support, bridge) with a toggle legend, and stats from `slice.json`.
- Rendering: one `THREE.LineSegments` per feature type, built once; a precomputed vertex
  offset per layer drives `drawRange`, so scrubbing does not rebuild geometry. The offset
  computation is a pure function in `model-core.js`.
- `layers.json`: `{bed, types, layers: [{z, h, segs: {type: [x0, y0, x1, y1, …]}}]}`,
  coordinates as integers in 0.01 mm. Budget 2 MB per model; if exceeded, decimate infill
  first.
- The parser (G-code → layers) lives in `slicer.py` as a pure function and reads Bambu
  `; FEATURE:` comments.
- The offline ZIP includes `layers.json`.

## Phases and acceptance

| Phase | Scope | Acceptance |
|---|---|---|
| P1 | `printkit` core, `models/` move, both models ported, `build.py` split, orphan files removed, rename references | Baseline captured from the current commit: every part's world-space bounds match within 0.001 mm and volume within 0.01 %; `model.json` fields other than `$schema`, `downloads` and part `position`/`rotation`/`meshes` identical; all checks in both `verification.json` still pass; tests green |
| P2 | `printability.py` | Synthetic-mesh tests pass; both models report printability; no orientation warnings on current print rotations, or each warning is explained in the model README |
| P3 | Spike, `printers/`, `slicer.py`, `slice` command | Both models produce a `.gcode.3mf` that opens in Bambu Studio; `printInfo` stats come from `slice.json` |
| P4 | `print-preview.js`, schema field, bundle | Browser check: gallery → model → In → scrub slider → screenshot, no console errors; `layers.json` ≤ 2 MB per model; works from the offline ZIP |

Phases run in order; each starts only after the previous one meets its acceptance.

## Error handling

- CAD: invalid BRep, multiple solids, non-watertight mesh, or failed check → non-zero
  exit, no files written, message names part and check.
- Catalog: schema or reference errors → `build` fails with the model id.
- Slicer: missing binary, CLI non-zero exit, or unparseable G-code → `slice` fails; previous
  `print/` outputs are left untouched.

## Testing

- pytest without CadQuery: pose inverse round-trip, `dim()` geometry and label,
  overhang/bridge on synthetic meshes (cube → zero overhang; T-shape → known area),
  G-code fixture → layers, the 13 existing catalog and asset-version tests.
- pytest with CadQuery: P1 regression against the captured baseline.
- `node --test`: existing tests plus layer vertex offsets.
- Browser check for P4 as listed above.

## Out of scope

- Writing a slicer or Bambu 3MF metadata by hand.
- Printers other than the P1S 0.4 mm preset.
- Automatic thumbnails.
- Collision simulation while dragging in the viewer.
- Renaming the GitHub repository (owner action).

## Deviations recorded during P1/P2

- `checks.sweep` is not implemented: sweeps are built inside the models; add it when a third model needs it.
- The 18650 cell stays in its model; it moves to the library when a second model uses it.
- `esp-enclosures` URL references in `index.html`, `model.schema.json` and `README.md` stay until the owner renames the GitHub repository.
