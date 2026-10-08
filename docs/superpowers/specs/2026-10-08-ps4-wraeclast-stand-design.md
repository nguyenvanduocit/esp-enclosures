# PS4 vertical stand — Wraeclast Ruins — design

Model id `ps4-wraeclast-stand`, folder `firmware/enclosures/ps4-wraeclast-stand/`.

## Goal

A printable vertical stand for an original PS4 (CUH-1000A), dressed as Path of Exile
"Wraeclast ruins": broken stone pillars with engraved runes, a skull, a hanging chain.
All art is original geometry generated in code — no game assets, no PoE logo — so the
model can sit in the public `esp-enclosures` gallery next to the ESP32 enclosures.

## Fixed inputs

| Input | Value | Confidence |
|---|---|---|
| Console | CUH-1000A, 275 W × 53 H × 305 D mm, 2.8 kg | HIGH — playstation.com tech specs |
| Cooling | Intakes on both narrow side faces (305 × 53), exhaust at the back | MEDIUM — blog/forum sources; grille position on the side not measured |
| Printer | Bambu A1 / P1S / X1C, 256³ mm, 0.4 mm nozzle, PLA | HIGH — user |
| Toolchain | CadQuery 2.8.0, trimesh 5.1.1, manifold3d 3.5.4, Python 3.12 | HIGH — spike ran on this machine |

## Layout (world coordinates, mm, Z up)

The console stands on a narrow side face. Its envelope is the box
x ∈ [−26.5, 26.5], y ∈ [−152.5, 152.5], z ∈ [20, 295]. Front (disc slot, USB) faces −Y.
The box contains the real parallelogram profile, so clearance checks against it are
conservative and the slant never needs measuring.

Two identical **ruin sets**. The front set is centred at y = −92.5. The back set is the
same parts rotated 180° about Z, centred at y = +92.5. One set of STLs, printed twice.
Both sets stay inside y ∈ ±[52.5, 132.5], clear of the ports and the exhaust.

Set-local coordinates below (front set; its outer face is −Y local).

### Plinth — print, stone

- Lower step 170 (X) × 80 (Y) × 10, z 0–10. Upper step 160 × 72 × 10, z 10–20.
- Cradle walls x ∈ ±[27, 39], y ∈ [−25, 25], z 20–65. Broken, chipped top edges.
- Slot x ∈ [−27, 27] (console 53 + 0.5 per side) cut through the full Y length down to
  z = 6 to leave an air channel, except two support ribs y ∈ ±[14, 22] whose tops sit at
  z = 20 and carry the console.
- Pillar sockets: pockets 34.4 × 34.4, 6 deep (z 14–20), centred at x = ±60, y = 0.
- Underside: four Ø12 × 1.5 recesses for stick-on rubber bumpers at (±70, ±30).
- Rune band engraved on the lower step's outer (−Y) face.

### Tall pillar — print, stone (sits in the +X socket)

- 34 × 34 shaft, 4 mm vertical-edge chamfers. Bottom 6 mm is the exact socket tenon.
  A 40 × 40 base band sits on the plinth top (no contact with the cradle wall at x = 39).
- 210 mm tall from the socket floor (global top ≈ 224). Jagged broken top: 3–5 seeded
  wedge cuts in the top 30 mm. 5–8 seeded corner chips along the vertical edges, ≤ 6 deep.
- Rune column (6 original glyphs, 18 × 18, stroke 2.0, depth 1.5) on the +X and −Y faces.
- Chain hook on the +X face at local z ≈ 170: Ø6 peg, 20 long along +X, with a 45°
  gusset (4 wide) underneath so it prints upright without support.

### Stub — print, stone (sits in the −X socket)

- Same section and base band, 100 tall from the socket floor (global top ≈ 114).
- Top is a flat seat; rim chips only lower the rim, never rise above the seat.
- Ø8 × 6 peg centred on the seat for the skull.

### Skull — print, bone

- SDF in `art.py` → `Manifold.level_set` at 0.5 mm → `simplify(0.05)`.
- ≈ 44 (X) × 52 (Y) × 46 (Z), facing outward (−Y local). Jawless: cranium, brow ridge,
  deep eye sockets, nasal cavity, cheekbones, upper teeth row. Every feature ≥ 2 mm.
- Flat bottom at z = 0 with a Ø8.4 × 7 hole for the stub peg.

### Chain — print, iron

- 7 links, wire Ø4, centreline straight 10 + end radius 6 (inner width 8, so the Ø6 peg
  fits with 1 mm per side). Interlocked links overlap 0.4 mm so the chain is one solid.
- Top link lies in the YZ plane and hangs on the pillar hook; links alternate planes.
  The last link has a 2 mm gap cut — a broken chain.
- Print orientation: links at ±45° to the bed, lowest point on z = 0. Needs tree supports.

### Fit coupon — print, stone (not in the assembly)

Plinth ∩ box x ∈ [−45, 45], y ∈ [10, 26], z ∈ [0, 70]: one rib plus both cradle walls.
About 15 minutes of printing; the user tests it on the real console before the full print.

## Geometry pipeline

- `model.py`: CadQuery structure (blanks, exact cutters, pegs, chain, coupon) and
  `export_and_verify()` — the only I/O, same shape as
  `esp32-c3-supermini-18650/model.py:160`.
- `art.py`: pure functions returning `manifold3d.Manifold`, no I/O:
  `skull()` and `erode(shape, seed, amplitude, mask)`.
- Order for every stone part:
  1. CadQuery blank → Manifold.
  2. `erode`: refine to ~0.8 mm, displace vertices **inward only** along vertex normals by
     seeded multi-octave noise, amplitude ≤ 1.0 mm. Zero displacement within 1 mm of the
     bed face and inside masked regions. Inward-only means every clearance designed on
     nominal geometry stays valid after erosion.
  3. Union art (seeded chip / broken-top cuts happen before erosion), then `simplify(0.05)`.
  4. Subtract the exact cutters last: slot, rib tops, sockets, tenons, bumper recesses,
     rune grooves. Functional faces are never touched by noise or simplify.
- Fixed seeds: re-running produces byte-identical STLs.
- `enclosure.step` = the mechanical core (CadQuery solids before erosion and art). The
  schema requires `downloads.step`; this is the part someone would edit.

## Verification (`verification.json`, asserts stop the script)

Per printable part: watertight, consistent winding, exactly one shell, volume > 0;
fits 250 × 250 × 250 in print orientation; ≤ 60k triangles.

Assembled pose (`overlap()` as in the existing models):
- No part intersects the console envelope; ribs only touch it.
- Air channel x ∈ [−26.5, 26.5], z ∈ [6, 20] outside the rib footprints, and the whole
  region under the console between the sets, are empty.
- Port/exhaust zones y ∈ [−212.5, −152.5] and [152.5, 212.5], x ∈ [−90, 90], z ∈ [0, 300]
  are empty.
- No two parts overlap; tenons and pegs clear their sockets/holes.
- Tipping angle from the combined centre of mass (console 2.8 kg + PLA parts at
  1.24 g/cm³) over the support polygon of both plinths ≥ 20°.

Repo level: `uv run build.py`, `node --test tests/*.test.js`,
`uv run --with jsonschema==4.23.0 python -m unittest discover -s tests`, then load
`#model/ps4-wraeclast-stand` in a browser: renders, no console errors, drag works.

Not checkable in code, documented in the README: overhangs and minimum wall thickness
(slice in Bambu Studio), load capacity (no FEA), `physical_fit_tested: false`.

## Viewer manifest

- Parts: per set plinth, tall pillar, stub, skull, chain (10 print parts) plus the console
  as a `box` primitive reference. Colours: stone `#7a746b`, bone `#d9cfb4`,
  iron `#3d3d42`, console `#1b1b1f`.
- Drag: plinth down, pillars/stub/skull/console up, chain outward.
- One assembly animation: console lifts out, skulls and chains come off, pillars rise,
  back to the assembled pose.
- Measurements: slot 54, air gap 20, plinth footprint 170 × 80, tall pillar height,
  overall height with console.
- `printInfo` and README in Vietnamese, matching the existing models; status "chưa in thử".

## Controller altars

Each set holds one DualShock 4 on a stone altar beside its plinth. The DS4 envelope is
162 (W) × 57 (T) × 100 (D) mm, 210 g — the largest of the published figures
(MEDIUM; sources list 161–162 × 52–57 × 98–100). Only this box is used, never the
controller's real contour.

The altar sits on the **stub side** (−X local): the tall-pillar side is taken by the
chain, which hangs at world x ≈ 84–100. Front altar is front-left, back altar back-right.

### Altar — print, stone (separate part, its own bumpers, stands on the desk)

Set-local coordinates as above (front set, stub side −X):

- Footprint x ∈ [−180, −86], y ∈ [−59, 123] (world y of the front altar ≈ [−151.5, 30.5]:
  aligned with the console front, clear of the port zone). Base slab z 0–10.
- Joint: a tongue 39.6 × 19.8 × 5.6 (y ∈ ±19.8, z 0–5.6, on the bed) runs from the
  altar's +X end into a pocket cut in the plinth's −X end, x ∈ [−85, −65], y ∈ [−20, 20],
  z ∈ [0, 5.8], open underneath (0.2 clearance on the sides, top and end). The joint sits
  on the bed because a tongue floating at z 2.2 would be a 21.8 mm cantilever (835 mm² of
  overhang) needing support. The tongue only locates; each piece carries its own load.
- Cradle: the DS4 leans back at 70° from horizontal with its face outward (−X) and its
  top toward the plinth. In the box frame, v = (cos 70°, 0, sin 70°) runs from the grips
  to the top and n = (−sin 70°, 0, cos 70°) is the face normal. The grip ends rest on a
  seat face perpendicular to v (20° from horizontal), solid wedge underneath. The back
  rests on a backrest parallel to the u–v plane, 8 thick, reaching 60 % of D along v, so
  the top edge and its micro-USB port stay free for charging. A 10 mm lip in front of the
  grips stops them sliding out. The back-bottom edge of the box is at x0 ≈ −118,
  z = 10.2; tune x0 so the backrest stays at x ≤ −88.
- Side cheeks at both Y ends: broken mini-pillars, 8 thick, 2 mm clear of the box, with
  jagged tops at most 60 high.
- Same art treatment as the plinth: seeded chips, inward-only erosion, a rune band on the
  outer (−X) face. Exact surfaces (seat, backrest, lip, tongue, bumper recesses) are cut
  after erosion.
- Underside: four Ø12 × 1.5 bumper recesses.

### Added verification

- Altar: watertight, one shell, fits 250³, ≤ 60k triangles.
- The DS4 envelope in its pose intersects no part, and rests on the seat and the backrest
  (contact > 0 after a 0.5 mm drop along −v).
- Tongue clears the pocket. The altar intersects no other part (plinth, stub, skull,
  chain, pillar, console).
- Port and exhaust zones are still clear.
- Tipping: the centre of mass includes both controllers (2 × 210 g). The support polygon
  is still only the plinth bumpers, because the altars are not rigidly attached. Must
  stay ≥ 20°.
- Altar alone: the controller's centre of mass projects inside the altar's bumper
  polygon.

### Viewer

- Add altarFront and altarBack (stone), plus ds4Front and ds4Back as `box` reference
  parts, colour `#2a2a30`.
- Drag: altars slide outward along ∓X; controllers lift out along +v. Dragging is
  illustrative and does not simulate collisions, as in the other models: a controller
  dragged more than 19 mm with the skull still in place passes through the skull.
- Animation: skulls, chains and controllers come off together, then the altars slide
  out, then the console and pillars; the stubs rise 7 mm. `build.py:86-93` limits each
  animated part to its single drag axis, and the +v axis points toward the skull and stub,
  so the controllers can't follow the real two-step path (over the lip, then outward).
  The animation is collision-checked with no part moving more than 1 mm per sample.
- Measurements: altar footprint, lean angle 70°.
- Update gallery dimensions, README, printInfo (altar: no supports expected, check the lip
  in the slicer), thumbnail and the ZIP.

## Non-goals

Game-extracted or fan-made meshes, the PoE logo, PS4 Slim/Pro variants, collision
simulation, FEA, editing the shared viewer, schema, or `build.py`.
