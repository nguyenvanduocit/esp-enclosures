# Procedural art in printkit

Goal: agents in this repo can make 3D art models (weathered stone, SDF sculpture, runes,
chains), not only enclosures, with the same `model.py` → `printkit cad` workflow.

Source: the PS4 "Wraeclast ruins" stand built in the `myhome` repo before printkit existed
(`myhome/firmware/enclosures/ps4-wraeclast-stand/`, handoff
`myhome/docs/handoff/2026-10-08-procedural-3d-art-for-esp-enclosures.md`). It is ported as
`models/ps4-wraeclast-stand/` and is the acceptance test.

## What moves into printkit

Only generic infrastructure. Model-specific art (skull, glyph table, chain, altar, chips)
stays in the model folder.

`printkit/art.py`, pure functions over `manifold3d.Manifold` and numpy, no file I/O:

| Function | Purpose |
|---|---|
| `length`, `ellipsoid`, `capsule`, `round_box`, `triangle_2d` | SDF primitives, negative inside |
| `smin`, `smax` | Polynomial smooth union / intersection |
| `level_set(distance, bounds, edge)` | Mesh an SDF; handles manifold3d's inverted sign |
| `weathering(points, seed)` | Seeded multi-octave value noise in [0, 1] |
| `mask_weight(points, mask)` | 0 near the bed and inside protected boxes, 1 elsewhere |
| `erode(shape, seed, amplitude, mask)` | Inward-only displacement along smoothed normals |
| `to_manifold(cq_shape)` | CadQuery solid → Manifold with a canonical vertex/face order |
| `canonical_mesh(shape)` | Vertices and triangles in a fixed order, planar regions retriangulated |

## Mesh-backed print parts

`@model.part` builds may return a `manifold3d.Manifold`:

- `export` checks `status()`, one shell, volume > 0, rotates it by `print_rotation`, puts
  it on the bed, writes the STL from `canonical_mesh` so the bytes are reproducible, then
  runs the same watertight / winding / single-body test and `assess()` as CadQuery parts.
- Eroded and SDF surfaces have no clean BRep. `model.part(..., core=fn)` names a function
  that returns the CadQuery *mechanical core* in the same installed pose; the core goes into
  `assembly.step`. A mesh part without `core` is left out of the STEP. The schema keeps
  requiring `downloads.step`, so a model needs at least one BRep or core.
- `checks.overlap(a, b)` accepts CadQuery or Manifold on either side. If either is a
  Manifold, both become Manifolds and the result is the boolean intersection volume.

## Copies

The stand has a front and a back set that share each STL. `model.copy(id, label, of=...,
rotation=..., position=...)` declares a print part placed by a rigid transform of another
part. It writes no STL: its `meshes[].src` points at the original's STL, its pose is the
transform composed with the original's pose, and its core (if any) goes into the STEP. It
returns a cached function giving the transformed installed shape for checks. This needs no
schema or viewer change: `src` values may repeat.

## Print-only parts

`model.part(..., assembled=False)` exports an STL and printability for a part that is not
part of the assembly (the fit coupon). Its build returns the shape in the print frame. It is
left out of `model.json`, the STEP and the viewer. `verification.json` lists it under
`parts`, and the stale-file cleanup reads that list as well as `model.json`.

## Not changed

- Viewer and `model.schema.json`.
- Single-axis removal (`printkit/catalog.py:96-103`). The stand's animation already moves
  every part along its one drag axis.
- CadQuery parts and the two existing models: same STL path, same verification keys.

## Port mapping

| Reference (`export_and_verify`) | printkit |
|---|---|
| `printable` dict, `write_stl` | `@model.part` returning Manifold; `model.copy` for the back set |
| `fit_coupon` | `model.part(..., assembled=False)` |
| `enclosure.step` from `cores` | `core=` on each part; file name becomes `assembly.step` |
| console, DS4 boxes | `model.reference`; the 20° DS4 box is a `Solid` piece |
| inline asserts + `report["checks"]` | one `@model.check` per reference check name |
| `model_json_poses_match` | Check re-derives each viewer pose with `printkit.pose` and maps the print-frame mesh onto the CAD shape |

## Verification

- All 25 reference check names present in `verification.json`, numbers equal to the
  reference where the geometry is the same.
- `printkit cad ps4-wraeclast-stand` twice → identical STL hashes.
- `uv run pytest && node --test tests/*.test.js`, `uv run printkit build`.
