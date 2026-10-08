# Bambu Studio CLI spike (P3 slicing, P4 preview)

Date: 2026-10-08. Question: can the Bambu Studio CLI slice this repo's STLs for a Bambu Lab P1S, and what does its output look like?

Confidence labels: HIGH = verified by command output in this spike, MEDIUM = inferred, LOW = guess.

## Environment

| Item | Value | Evidence |
|---|---|---|
| Bambu Studio | 02.08.02.61 | `PlistBuddy -c "Print CFBundleShortVersionString" /Applications/BambuStudio.app/Contents/Info.plist` prints `02.08.02.61` |
| Binary | `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio` (277 MB) | `ls -l` |
| Profiles | `/Applications/BambuStudio.app/Contents/Resources/profiles/BBL/{machine,process,filament}` | `ls` |
| Host | macOS 26.4.1 arm64, Python 3.12.8 | `sw_vers`, `uname -m` |
| Machine preset | `Bambu Lab P1S 0.4 nozzle.json` | `ls .../machine \| rg P1S` |
| Process preset | `0.16mm Optimal @BBL X1C.json` (no P1S-named process file exists; the X1C file lists `Bambu Lab P1S 0.4 nozzle` in `compatible_printers`) | python read of `compatible_printers` |
| Filament preset | `Bambu PLA Basic @BBL P1S 0.4 nozzle.json` | `ls .../filament \| rg "Bambu PLA Basic"` |
| Scratch | `/tmp/spike/` only | |

`--help` (100 lines, `/tmp/bambu-help.txt`) lists `--slice`, `--export-3mf`, `--load-settings`, `--load-filaments`, `--arrange`, `--orient`, `--rotate[-x|-y]`, `--outputdir`, `--export-settings`, `--info`. It prints one trace line (`Initializing StaticPrintConfigs`) and no progress on a normal run.

## Results

Test inputs: `models/esp32-c3-supermini/{base,lid}.stl`, `models/esp32-c3-supermini-18650/{base,batteryLid,electronicsLid,usbCap}.stl`. Command shape in every row (`$F` holds machine.json, process.json, filament.json):

```
BambuStudio --load-settings "$F/machine.json;$F/process.json" --load-filaments "$F/filament.json" \
  --arrange 1 --slice 0 --export-3mf out.3mf <stl...>
```

| Question | Answer | Evidence | Conf. |
|---|---|---|---|
| Does the CLI accept system presets directly (Step 3)? | It exits 0 and writes a 3mf, but the `inherits` chain is not resolved. Only the leaf file's own keys apply, the rest are built-in defaults. The output is wrong without any error. | Leaf process file has 50 keys and no `layer_height` (parent `fdm_process_single_0.16` has 0.16). Output: `layer_height '0.2'`, `wall_loops '2'`, `sparse_infill_pattern 'cubic'`, `; total layer number: 92`, `; total filament weight [g] : 0.00` (leaf filament has no `filament_density`). `print_settings_id` still says `0.16mm Optimal @BBL X1C`, so the metadata lies. | HIGH |
| Does a flattened preset (inherits merged parent to child) work? | Yes, with `"from": "system"`. Same files with `"from": "User"` fail: exit 239, `run 3002: process not compatible with printer.`, and `result.json` says `The selected printer is not compatible with the process preset in the 3mf.` (`return_code -17`). Emptying `compatible_printers` did not help, so `from` is the trigger. | Recipe below. Flat A: `layer_height '0.16'`, `initial_layer_print_height '0.2'`, `sparse_infill_density '15%'`, `grid`, `brim_width '5'`, `; total layer number: 115`, `; total filament weight [g] : 6.51`. | HIGH |
| Are the process overrides applied? | Yes. Set in the flattened process JSON: `layer_height 0.16, wall_loops 3, sparse_infill_density 15%, sparse_infill_pattern gyroid, enable_support 0`. `Metadata/project_settings.config` of the output: `{'layer_height': '0.16', 'wall_loops': '3', 'sparse_infill_density': '15%', 'sparse_infill_pattern': 'gyroid', 'enable_support': '0'}`. G-code changed accordingly (weight 6.51 g to 6.68 g, Sparse infill 68 to 1 blocks). | `/tmp/spike/inspect.sh ovA.3mf` | HIGH |
| Do all eight spec keys exist and take effect? | Yes. Probe B with every value different: `layer_height '0.12'`, `initial_layer_print_height '0.24'`, `wall_loops '4'`, `sparse_infill_density '8%'`, `sparse_infill_pattern 'gyroid'`, `enable_support '1'`, `brim_type 'outer_only'`, `brim_width '6'`. G-code: 152 layers, `; FEATURE: Brim` appears. Values are JSON strings. | `/tmp/spike/inspect.sh ovB.3mf` | HIGH |
| Can overrides be passed as a third file? | No. A second process-type file is rejected. P3 must edit the flattened process JSON. | `--load-settings "m;p;overlay.json"` prints `duplicate process config file: /tmp/spike/overlay.json`, exit 251. An overlay without `from` prints `file ... 's from  unsupported` and `run found error, exit`; `result.json` then holds `return_code -5`, `The input preset file is invalid and can not be parsed.` (shell exit code not captured) | HIGH |
| Is estimated time in the G-code header? | Yes, line 1-5 of the header block: `; model printing time: 16m 30s; total estimated time: 16m 50s`. Also `slice_info.config` has `<metadata key="prediction" value="1010"/>` (seconds). | `head -20 plate_1.gcode` | HIGH |
| Is filament weight in the header? | Yes with a flattened filament preset: `; total filament weight [g] : 6.51`, `; total filament length [mm] : 2146.90`. Also `slice_info.config`: `<filament ... used_m="2.15" used_g="6.51" used_for_support="false"/>` and plate `<metadata key="weight" value="6.51"/>`. Direct system presets give `0.00` (see row 1). `total filament volume [cm^3]` looks wrong (5163 for 2.1 m of filament); treat as unusable. | header + `slice_info.config` | HIGH (volume: MEDIUM that it is wrong) |
| `; FEATURE:` names | `Bottom surface, Bridge, Custom, Floating vertical shell, Gap infill, Inner wall, Internal solid infill, Outer wall, Sparse infill, Top surface` (flat A, base.stl). Extra with support/brim/skirt: `Support`, `Support interface`, `Overhang wall`, `Brim`, `Skirt`. Counts for base.stl at 0.16 mm: Outer wall 424, Inner wall 419, Internal solid infill 387, Gap infill 268, Sparse infill 68, Top surface 14. Flipped upside down with support on (`--rotate-x 180`, probe B settings): `Support 150`, `Support interface 23`, `Overhang wall 21`, `Bridge 4`. Each block is followed by `; LINE_WIDTH: <mm>`. These names are the P4 colour legend. | `rg -o "^; FEATURE: .*" plate_1.gcode \| sort \| uniq -c` | HIGH |
| Layer-change marker | `; CHANGE_LAYER`, followed by `; Z_HEIGHT: 0.36` and `; LAYER_HEIGHT: 0.16`; later `; layer num/total_layer_count: 1/115`. `;LAYER_CHANGE` (Prusa style) is absent: `rg -c "^;LAYER_CHANGE"` returns nothing. `rg -c "^; CHANGE_LAYER"` = 115 = `; total layer number: 115`. | `rg -n -A3 "^; CHANGE_LAYER"` | HIGH |
| G-code size per plate | base.stl: 1.10 MB (0.16 mm), 1.18 MB (flat A). base+lid: 1.39 MB. four-part 18650 plate: 2.25 MB. Upside-down with support at 0.12 mm: 2.73 MB. The 3mf itself is 180-650 KB (zip). | `ls -l`, `wc -c`; extrusion moves: 18.9k (base), 24.7k (two), 44.1k (four), 43.2k (support probe) | HIGH |
| Per-object weight on a two-part plate | Not reported. `slice_info.config` has one plate weight (`8.70`) and one aggregate `<filament used_g="8.70">`; `<object>` entries carry only `identify_id`, `name`, `skipped`. Header has only totals. Workaround A: slice each part alone (about 1 s each): base alone 6.68 g (ovA settings), both 8.70 g. Workaround B: the G-code has per-object blocks (`; start printing object, unique label id: 47` ... `; stop printing object, unique label id: 47`, 141 blocks in the two-part plate) so extrusion length per object can be summed from the G-code. | `unzip -p two.3mf Metadata/slice_info.config`; `rg -n "start printing object" ` | HIGH (absence), MEDIUM (workaround B untested beyond marker existence) |
| Object-to-id mapping | `Metadata/plate_1.json` lists `bbox_objects` with `name` and `bbox` per object (bed coordinates); G-code carries `; OBJECT_ID: <id>`; `slice_info.config` has `<object identify_id>`. Ids in `plate_1.json` (73, 74) differ from the G-code ids (47, 58) in the same run, so match by bbox, not by id. | `unzip -p two.3mf Metadata/plate_1.json` | MEDIUM (id mismatch observed in one run) |
| Slice wall time | base: 1.07 s (0.91 s for B); two-part: 1.02 s; four-part: 1.25 s; support probe: 1.57 s; direct (wrong) preset: 1.15 s. Cold start included. | `/usr/bin/time -p` | HIGH |
| Error reporting | Errors exit non-zero (239, 251 observed) with one stderr line and write `result.json` into the **current directory** (`error_string`, `return_code`). Success writes no `result.json`. | `ls` in empty cwd after a failing and a passing run | HIGH |
| Orientation advice | `--orient 1` runs the auto-orient search and logs candidates with costs to stderr (`orientation: 0.7071 -0.0000 -0.7071, cost: ...`, `best: -0.000000 -0.000000 1.000000, costs: 0.0, 1255.6, 837.1, 141.7, ...`). For base.stl it kept the current orientation (identity rotation in `3D/3dmodel.model`). The 7 cost columns are not documented. `--rotate-x 180` applied a rotation and produced support (row FEATURE). | `--orient 1` run, `rg -o 'transform=...'` | MEDIUM (cost semantics unknown) |
| Does `--arrange 1` move the part? | Yes. Output G-code is in bed coordinates, object centred at about (128,128) for one part (`transform="... 127.99999 128 9.2"`), side by side for several. STL-local XY is not preserved. | `3D/3dmodel.model` transform | HIGH |

### Flatten recipe (verified)

Merge parent to child by `name` within the same type directory, drop `inherits` and `instantiation`, set `from` to `system`:

```python
import json, os
P = "/Applications/BambuStudio.app/Contents/Resources/profiles/BBL/"
def index(t):
    m = {}
    for f in os.listdir(P + t):
        if f.endswith(".json"):
            try: d = json.load(open(P + t + "/" + f))
            except Exception: continue
            m[d.get("name")] = d
    return m
def flatten(t, name):
    idx = index(t); d = idx[name]; chain = [d]
    while d.get("inherits"):
        d = idx[d["inherits"]]; chain.append(d)
    out = {}
    for c in reversed(chain): out.update(c)
    out.pop("inherits", None); out.pop("instantiation", None); out["from"] = "system"
    return out
```

Chains resolved: machine `Bambu Lab P1S 0.4 nozzle` <- `fdm_bbl_3dp_001_common` <- `fdm_machine_common` (113 keys); process `0.16mm Optimal @BBL X1C` <- `fdm_process_single_0.16` <- `fdm_process_single_common` <- `fdm_process_common` (196 keys); filament `Bambu PLA Basic @BBL P1S 0.4 nozzle` <- `Bambu PLA Basic @base` <- `fdm_filament_pla` <- `fdm_filament_common` (139 keys, `filament_density 1.26`). Script: `/tmp/spike/flatten.py` (the `from` value there was still `User`; `/tmp/spike/flatA/` holds the working set).

## Decision

1. **Preset source for P3: flatten Bambu Studio's bundled system profiles at slice time** (the recipe above), write the three JSON files to a temp dir, apply the user's overrides to the process JSON, and run the CLI with them. Reasons:
   - Step 4 (user exports presets from the GUI) is not needed; the CLI works unattended (HIGH).
   - Direct system presets silently produce wrong output (HIGH), so P3 must never pass unflattened files.
   - No checked-in copy of the presets: they track the installed Studio version, so profile updates arrive with the app. A copy in the repo would drift (MEDIUM).
2. **Override mechanism:** edit keys in the flattened process JSON (values as strings). The CLI accepts only one process file, so no overlay file (HIGH). After slicing, P3 should read `Metadata/project_settings.config` from the 3mf and compare the requested keys, failing loudly on mismatch. The same check would have caught the silent default-settings result in row 1.
3. **Process preset name:** use the X1C-named `0.16mm Optimal @BBL X1C` file; it lists the P1S 0.4 nozzle as compatible. Flattening works by name, so the layer-height variants (`0.20mm Standard @BBL X1C` etc.) use the same code path (MEDIUM, other variants not sliced).
4. **P3 summary data:** read time and weight from `; total estimated time:` and `; total filament weight [g]:` in the G-code header, or from `Metadata/slice_info.config` (`prediction` seconds, `used_g`), which is easier to parse as XML. Per-part numbers: slice each part separately (about 1 s each), then slice the combined plate for the plate total.
5. **P4 preview from G-code:** parse `; CHANGE_LAYER` / `; Z_HEIGHT` / `; LAYER_HEIGHT`, `; FEATURE:` for colour classes (incl. `Support`, `Support interface`, `Overhang wall`, `Bridge`, `Brim`, `Skirt`), `G1/G2/G3` with `E>0` for extrusion segments. Moves use bed coordinates (see Open issues). `layers.json` size, measured on the four-part plate (2.25 MB G-code, 44k extrusion segments, 158 layers) with a naive per-segment `[feature,x0,y0,x1,y1]` encoding at 2 decimals: 2.03 MB raw, 178 KB gzipped (HIGH, prototype run). A per-feature polyline encoding would drop the raw size by roughly half (LOW, not built). Estimate for P3: layers.json is about 0.9x the G-code size raw, so 1 to 3 MB per plate, under 0.7 MB gzipped. Support-heavy plates are the upper bound (the support probe gzips to 600 KB G-code alone).
6. **Orientation advice** (user goal "đặt góc nào ok, support ra sao"): feasible by slicing candidate rotations (`--rotate-x/-y`) and comparing weight, time and `Support` feature counts, about 1 to 2 s per candidate (HIGH for the mechanism, the candidate set is a P3 design choice). `--orient 1` output is a possible shortcut but its costs are undocumented (MEDIUM).

## Open issues

- `from: "User"` is rejected as incompatible even with matching names. Cause inside Studio unknown; `from: "system"` is a workaround for a loader rule, not documented behaviour. P3 needs a test that slices a known STL and asserts `layer_height` in `project_settings.config`, so a Studio update that changes this fails loudly (MEDIUM).
- Studio writes `result.json` to the current directory on failure. P3 must run the CLI with `cwd` set to a temp dir to keep the repo clean (HIGH; observed once when a failed run left `result.json` in the repo root, since deleted).
- Exit codes seen: 239 (incompatible preset), 251 (duplicate process file). `result.json.return_code` differs from the shell exit code (-17 vs 239). Not a documented set; P3 should treat any non-zero as failure and surface `result.json.error_string` (MEDIUM).
- `plate_1.json` object ids differ from the G-code `OBJECT_ID`s, and `plate_1.json` reports `layer_height 0.2` per object while the slice used 0.16. Do not use those fields; use `project_settings.config` and the G-code (MEDIUM).
- `--arrange 1` changes XY. P4 either draws in bed coordinates (bed 256 x 256 for the P1S, MEDIUM, from the machine profile's usual size, not read in this spike) or subtracts the object bbox from `plate_1.json`.
- Only PLA Basic, 0.4 nozzle, 0.16 mm Optimal were sliced. Other filaments/nozzles: not tested. No non-PLA temperatures, no multi-colour, no tree support (default `support_type` of the preset applies; the support probe used the preset default) tested.
- Support quality, bridging and overhang results were checked only by FEATURE counts, not visually. Per-object weight from G-code extrusion sums (workaround B) is not implemented.
- The CLI prints almost nothing on success; there is no progress output to parse. `--pipe` exists (progress to a named pipe), untested.
