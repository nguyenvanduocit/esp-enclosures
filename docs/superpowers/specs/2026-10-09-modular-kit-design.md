# Modular kit: standard and first six modules

Date: 2026-10-09. Status: design agreed with the user through a 3D spike (`docs/superpowers/explore/kit_spike.py`, 36 geometry checks on real CAD); this document is the contract for the implementation plan `docs/superpowers/plans/2026-10-09-modular-kit.md`.

## Goal

Replace the one-off enclosures (V1 `esp32-c3-supermini`, V2 `esp32-c3-supermini-18650`) with a kit of separate printed modules that attach on any side with magnets and pass wires through the joint. Every module is one model in the web app: ESP32 mini, battery with charger, display and three sensors. A written standard fixes size, joint and wire port, so a new module only declares its own interior.

## Decisions taken (all from the user, through the spike)

| Topic | Decision |
|---|---|
| Grid | 20 mm units; a module is `a × b × c` units; outer size per axis `n·20 − 0.2` (0.1 mm clearance per side) |
| Walls | 2.0 mm everywhere, lid plate included. Nothing stands out of any surface; the interior is flat (no bosses or ridges around the pockets) |
| Connector | One at the centre of **every unit on every side**: a wire port Ø5 through the wall plus pockets drilled from outside, all parts glued flush |
| `+` faces | 4 round magnets 5×1.5 on a ring of radius 5.9 around the port (at 45°, 135°, 225°, 315°); pockets Ø5.1 × 1.5 deep |
| `−` faces | one carbon-steel M6 flat washer (12 / 6.4 / 1.6, DIN 125) in a counterbore Ø12.1 × 1.6 around the port |
| Joint | Always magnet to steel (`+` face to `−` face). Two `+` faces push apart, two `−` faces do nothing. The washer is a ring, so a joint holds at any turn about its axis |
| Plain faces | Only where a function needs it: a display screen, a sensor window or vent |
| Lid | One face per module is the lid; it is also a connector face (plate 2.0 mm) unless declared plain (plate 1.8 mm) |
| Library | Shared geometry in `printkit/modules.py`; boards in `printkit/library/electronics.py`; one `models/<id>/model.py` per module |

Buy zinc-plated carbon-steel washers: stainless 304/316 washers are not magnetic.

## The standard (`printkit/modules.py`)

Millimetres, Z up. Module coordinates start at the outer corner `(0.1, 0.1, 0.1)`; the registered model is shifted so the module is centred in X/Y and sits on Z = 0.

| Constant | Value |
|---|---|
| `GRID`, `CLEAR`, `EDGE_R`, `WALL` | 20, 0.1, 1.0, 2.0 |
| `LID_PLAIN`, `LID_SKIRT`, `SKIRT_WALL`, `FIT` | 1.8, 2.4, 1.2, 0.2 |
| `DISC_D`, `DISC_T`, `DISC_R` | 5.0, 1.5, 5.9 (pocket Ø `DISC_D + 0.1`) |
| `WASH_OD`, `WASH_ID`, `WASH_T` | 12.0, 6.4, 1.6 (counterbore Ø `WASH_OD + 0.1`) |
| `PORT_D` | 5.0 |

- A pocket is as deep as the part it holds, so the part ends flush; the floor behind it is `WALL − depth` thick (0.5 mm behind a magnet, 0.4 mm behind a washer).
- The lid skirt (2.4 deep, 1.2 thick, inset `FIT` from every wall) hangs inside the cavity.
- Faces `+x +y +z` are `+`, faces `-x -y -z` are `−`.
- Print orientation: the shell prints with its open side up, the lid with its outer face down (`rot_up(face)`, `rot_down(face)`).

Measured on real CAD in the spike (CadQuery distances): pocket walls between pockets of adjacent faces of one unit 2.37 mm, between pockets of one face 3.24 mm, magnet pocket to wire port 0.85 mm; every magnet lies 48 % over the washer annulus; the gap between a joined magnet and washer is 0.20 mm; a Ø4.9 rod passes both ports and the washer bore.

## Modules

| Model id | Title | Units (x, y, z) | Lid | Plain / cut-outs | Interior |
|---|---|---|---|---|---|
| `kit-esp32` | Module ESP32-C3 mini | 2 × 2 × 2 | `+y` | USB-C slot in the `-y` wall, in the channel between the two connector rows | ESP32-C3 SuperMini on four posts, USB at mid height |
| `kit-battery` | Module pin 18650 + sạc | 3 × 4 × 2 | `+x` | USB-C slot in the `-y` wall, same channel | 18650 holder against `-x`, TP4056 USB-C charger on posts beside it |
| `kit-display` | Module màn hình 2.4" | 4 × 3 × 1 | `+y` | `+z` plain: 49 × 37 window | ILI9341 2.4" board under the window |
| `kit-bme280` | Module cảm biến BME280 | 1 × 1 × 1 | `+y` | `-y` plain: vent slots | GY-BME280 board on two ribs |
| `kit-mpu6050` | Module cảm biến MPU6050 | 2 × 2 × 1 | `+z` | none | GY-521 board on four posts |
| `kit-pir` | Module cảm biến PIR | 2 × 2 × 2 | `-z` | `+z` plain: Ø24.4 hole for the lens | HC-SR501 board, lens through the hole |

Assumptions the user has not confirmed (each module README repeats them):

- **A1.** The display is the 2.4" ILI9341 board, 70.5 × 43.3 mm, active area 48.96 × 36.72 mm.
- **A2.** "Pin kèm sạc" means an 18650 holder plus a TP4056 USB-C charger board with protection and no boost converter.
- **A3.** Sensors are GY-BME280 (≈ 15.4 × 11.6), GY-521 MPU6050 (≈ 20.5 × 16) and HC-SR501 (32 × 24, lens Ø23). Sizes come from shop listings and disagree by about 1 mm between sellers; the user measures before printing.

## Checks (registered on every module by `declare`)

1. Shell plus lid bounding box equals `outer(cells)` on every axis.
2. The lid does not touch the shell.
3. Every magnet and washer sits in its pocket without cutting the wall; none stands out of the outer box.
4. Every pocket is void at half depth, solid just beyond its floor, the wall behind it is empty (interior flat, ignoring declared posts), and every port is open through the wall.
5. Plain faces are solid wall outside their own cut-outs.
6. Cut-outs (USB slot, window) do not cut into any pocket.
7. Reference parts (board, holder, cell, display) clear the shell and the lid.

The library's own tests assert the pocket walls above (≥ 0.8 mm) and the 40 % minimum overlap of a magnet over a washer.

## Out of scope

- A multi-module assembly page or demo model.
- Electrical connectors, boost converters, load rating, waterproofing.
- Changes to `printkit` core, the viewer or the schema.

## Risks

| Risk | Confidence | Mitigation |
|---|---|---|
| Pull of a 5×1.5 magnet through 0.2 mm onto a 1.6 mm washer is unmeasured, and only 48 % of each magnet lies over the washer | LOW | print one joint and pull-test it before printing a full set |
| Magnets and washers are held by glue only; the 0.4 to 0.5 mm floor behind them does not resist the pull | MEDIUM | READMEs tell the user to glue every part |
| Filling every `+` pocket takes 4 magnets per unit-side (156 for the three spike modules); one joint needs only 4 | MEDIUM | READMEs list both numbers; fitting is by joint |
| Board sizes come from listings and disagree between sellers | MEDIUM | every README states the size used and asks for measurement |
| Counterbores on vertical walls print as horizontal holes and may sag | MEDIUM | `cad` prints overhang warnings; print one module first |
