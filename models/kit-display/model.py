"""Module màn hình 2.4": 4 x 3 x 1 units. ILI9341 board under a 48.96 x 36.72 window (the active area, zero margin) in the +z face,
held up against it by two snap hooks. Millimetres, Z up."""
from printkit.library.electronics import ILI9341_PCB, ili9341_24
from printkit.modules import WALL, ModuleSpec, Mount, Pcb, bounds, box, corner_stop, kit_model, snap_hook

CELLS = (4, 3, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX = (LO[0] + HI[0]) / 2
PY = LO[1] + WALL + 0.8 + 43.3 / 2                    # PCB 0.8 mm from the -y wall
GLASS_TOP = HI[2] - WALL - 0.2                        # glass sits 0.2 mm under the plain top wall
PCB_Z = GLASS_TOP - 3.2 - 1.6                         # PCB underside
WINDOW = box((CX - 24.48, PY - 18.36, HI[2] - WALL - 1), (CX + 24.48, PY + 18.36, HI[2] + 1))   # active area 48.96 x 36.72
PCB = Pcb((CX, PY, PCB_Z), ILI9341_PCB, held=-1)
# two beams from the -y wall along the +-x edges, barbs under the PCB at mid length; the -y wall lies on the bed, so the beams print upright.
# BEAM_BACK raises each 24.5 mm beam 1.2 mm above the PCB top: 3 mm tall, it bends (3 / 1.8)^3 = 4.6 times less under the hanging
# board than a beam only as tall as the PCB edge.
BEAM_BACK = 1.2
HOOKS = tuple(snap_hook(PCB, side, root=('y', LO[1] + WALL), back=BEAM_BACK) for side in ('+x', '-x'))
# two corner stops held out from the +-x walls stop the board 0.2 mm past its +y edge; the -y wall is 0.8 mm from its -y edge
BACK = tuple(corner_stop(PCB, '+y', wall=wall) for wall in (LO[0] + WALL, HI[0] - WALL))

model = kit_model(
    'kit-display', title='Module màn hình 2.4"',
    description='Màn hình TFT 2.4" ILI9341 dưới khung hiển thị 49×37 mm, khối 4×3×1.',
    spec=ModuleSpec(cells=CELLS, lid='+y', plain=('+z',), cuts=(WINDOW,), adds=tuple(h.solid for h in HOOKS) + BACK), color='#7b6cd9',
    refs=[('display', 'Màn hình ILI9341 2.4"', ili9341_24(at=(CX, PY, PCB_Z)))], boards=(Mount(PCB, 'display', HOOKS),),
    notes=['Mặt +z là màn hình nên không có điểm nối.',
           'Cửa sổ cắt đúng 48,96×36,72 mm, bằng vùng hiển thị và không chừa lề (gọi là 49×37 mm cho tròn); kính 60×40 mm là giả định, hãy đo màn hình của bạn.',
           'Bo lắp từ phía nắp +y: đưa bo vào dưới khung rồi đẩy lên, hai móc gài ở hai cạnh ngắn bật vào dưới mặt PCB.'])
