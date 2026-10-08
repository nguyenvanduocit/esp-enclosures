---
name: procedural-art
description: Use when a model in this repo needs art rather than plain enclosure geometry - weathered or broken stone, engraved runes or glyphs, chains, sculpted forms (skulls, organic shapes) built from SDFs, or any printkit part that returns a manifold3d Manifold instead of a CadQuery solid. Covers printkit/art.py, mesh-backed parts, model.copy, print-only coupons, and the checks art parts need.
---

# Procedural 3D art with printkit

Worked example, read it first: `models/ps4-wraeclast-stand/model.py` (weathered stone, runes, an SDF
skull, a chain, front/back sets, a fit coupon, 26 checks). Design note:
`docs/superpowers/specs/2026-10-08-procedural-art-design.md`.

## What code-made art does well

| Works | Weak |
|---|---|
| Weathered and broken stone, chipped corners, broken tops | Hand-sculpted organic detail (faces, creatures) |
| Engraved runes and glyphs | Anything that needs texture rather than shape |
| Chains, rings, hooks | |
| Stylised forms from blended primitives (a jawless skull) | |

An SDF skull reads as a smooth ball from behind. For more detail, sculpt elsewhere and import the mesh.
That loses rebuild-from-code. **IP:** the repo is public. Never use meshes, logos or text from a
game. Use only original geometry, or remixable community meshes with credit.

## API

```python
from printkit import Drag, Model, art
from printkit.shapes import placed

@model.part('stone', 'Đá', color='#7a746b', drag=Drag((0, 0, 1), 50),
            core=lambda: stone_blank())        # CadQuery core goes into assembly.step
def stone():
    shape = art.erode(art.to_manifold(stone_blank()), seed=11, amplitude=1.0, mask=[((-5, -5, -1), (5, 5, 7))])
    return shape.simplify(art.SIMPLIFY_TOL) - art.to_manifold(exact_cutters())

stone_back = model.copy('stoneBack', 'Đá sau', of='stone', rotation=(0, 0, 180))  # shares stone.stl

@model.part('coupon', 'Coupon', color='#7a746b', assembled=False)   # STL only, not in the viewer
def coupon():
    return stone() ^ art.box((-10, -10, 0), (10, 10, 20))
```

- **A build returns** a CadQuery solid or a `manifold3d.Manifold`, in its installed pose. Manifold
  STLs are written from `art.canonical_mesh`, so they are byte-identical across runs.
- **`core=`**: a mesh part has no BRep. Give it its CadQuery mechanical core, the shape before art,
  or `assembly.step` leaves it out. At least one part must have a BRep.
- **`model.copy`** reuses an STL under a rigid move. It returns the moved shape for checks.
- **`checks.overlap` / `clear`** accept CadQuery and Manifold in any mix.
- **`printkit.export.print_frame(shape, rotation)`** gives the exact mesh export will write. Measure
  triangles, bed fit and SHA in checks with it.
- **`printkit/art.py`**:
  - SDF primitives, negative inside: `ellipsoid`, `capsule`, `round_box`, `triangle_2d`.
  - Blends: `smin` and `smax`.
  - `level_set(distance, bounds, edge)` meshes an SDF.
  - Noise: `weathering(points, seed)` and `mask_weight`.
  - `erode`, `to_manifold`, `box` and `canonical_mesh`.

## Recipes

- **SDF sculpture**:
  1. Write `distance(p)` from primitives, combined with `smin` (blend) and `smax(d, -cut, k)` (carve).
  2. `art.level_set(distance, bounds, art.MESH_EDGE)`.
  3. `trim_by_plane` for a flat base.
  4. `.simplify(art.SIMPLIFY_TOL)`.
  5. Subtract an exact peg hole.

  Keep features ≥ 2 mm. Measured: 0.5 mm edge on a 60×70×65 mm box gives 579k triangles in 10 s, and
  simplify(0.05) brings that to 17k.
- **Stone**, in this order (`stone()` in the example):
  1. CadQuery blank.
  2. Seeded wedge chips and broken tops (`random.Random(seed)`).
  3. `art.erode`.
  4. Union the exact additions.
  5. `simplify(0.05)`.
  6. Subtract the **exact cutters last**: slots, sockets, lips, bumper recesses.

  Functional faces never see noise or simplify.
- **Erosion is inward only**, so every clearance designed on nominal geometry stays valid. Mask
  functional regions with boxes. `erode` already protects the 1 mm next to the bed.
- **Flat seats**: simplify sagged a seat by 0.015 mm. Build the blank 2 mm proud and trim it exactly
  (`ceiling=`). Lips: overfill them, then cut every face after erosion.
- **Runes**: a stroke table plus `slot2D` grooves 1–1.5 mm deep. Cut them after erosion, with cutters
  that reach past the eroded surface. Every glyph costs triangles.
- **Chains**: sweep a circle along a stadium path. Overlap links by 0.4 mm so the chain is one
  solid. Print the links at ±45° to the bed, with tree supports.

## Pitfalls

1. **Touching faces count as overlap** after float32 rounding. Leave 0.02 mm at contacts and prove
   contact separately: drop the part 0.5 mm and require overlap > 0.
2. **Measure "inward only" on the final mesh**, not only after the erosion step. Simplify adds
   0.004–0.05 mm³ outside. Assert < 0.5 mm³ and name the check honestly.
3. **One drag axis per part** (`printkit/catalog.py`). Every keyframe must lie on it, so
   "lift over the lip, then pull out" cannot be animated. Reorder the animation instead.
4. **Sample animations** so no part moves more than 1 mm per step (`animation_samples` in the
   example). 81 samples let a part jump 10 mm.
5. **Budget**: ≤ 60k triangles per part. Edge 0.5 mm, simplify 0.05 mm (far below a 0.16 mm layer).
   The full example builds in about 1 minute.
6. **STEP is not byte-reproducible** (it has a timestamp). Run `uv run printkit build` after the last
   `cad` so the ZIP matches.
7. `uv run` can stall in this repo while another process holds the environment. `.venv/bin/printkit`
   and `.venv/bin/python -m pytest` run the same code.

## Verify before claiming done

- `uv run printkit cad <id>` twice, then `shasum -a 256 models/<id>/*.stl` on each run. The hashes must
  match.
- Checks for art parts:
  - Watertight, one shell, ≤ 60k triangles, fits the bed. Use `print_frame`.
  - Pairwise overlap against every part and hardware envelope.
  - Clearance zones.
  - Contact by drop.
  - Erosion outside nominal.
  - Tipping, if the model stands.
  - Animation collision.
- `uv run printkit build && uv run pytest && node --test tests/*.test.js`.
- Have a separate reviewer agent re-measure the STLs and try to break each claim.
