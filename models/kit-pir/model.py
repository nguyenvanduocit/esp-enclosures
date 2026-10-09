"""Module cảm biến PIR: 2 x 2 x 2 units. HC-SR501 hangs from the ceiling on two snap hooks, its lens passes through a hole in the +z
face. Millimetres, Z up."""
import itertools

from printkit.library.electronics import HC_SR501_PCB, hc_sr501
from printkit.modules import WALL, ModuleSpec, Mount, Pcb, bounds, cyl, kit_model, snap_hook

CELLS = (2, 2, 2)
LO, HI = bounds(ModuleSpec(CELLS, '-z'))
CX, CY = (LO[0] + HI[0]) / 2, (LO[1] + HI[1]) / 2
LENS_TOP = HI[2] - 0.9                                 # the lens ends 0.9 mm under the outer top face
BOARD = (CX, CY, LENS_TOP - 19.2)                      # PCB underside; PCB 1.2 thick plus 18 mm lens
CEILING = HI[2] - WALL
HOLE = cyl((CX, CY, HI[2] - WALL - 1), (0, 0, 1), 12.2, WALL + 2)          # O24.4 for the O23 lens
HANGERS = tuple(cyl((CX + sx, CY + sy, BOARD[2] + 1.2), (0, 0, 1), 1.5, CEILING + 0.5 - (BOARD[2] + 1.2))
                for sx, sy in itertools.product((-13, 13), (-9, 9)))
PCB = Pcb(BOARD, HC_SR501_PCB, held=-1)
# Two stems hang from the ceiling at the +-y edges and hold the PCB underside up against the hangers. They sit 4.8 mm off the
# centre in x, point-symmetric: 0.32 mm outside the lens hole cutter (r 12.2) and 0.7 mm clear of the +-y port paths. Their roots
# are not rounded, because the inner fillet would reach into the lens hole cutter. The lens in its hole stops the board in x.
HOOKS = (snap_hook(PCB, '+y', root=('z', CEILING), at=CX + 4.8, fillet=0),
         snap_hook(PCB, '-y', root=('z', CEILING), at=CX - 4.8, fillet=0))

model = kit_model(
    'kit-pir', title='Module cảm biến PIR',
    description='Cảm biến chuyển động HC-SR501, thấu kính nhô qua lỗ ở mặt trên, khối 2×2×2.',
    spec=ModuleSpec(cells=CELLS, lid='-z', plain=('+z',), cuts=(HOLE,), adds=HANGERS + tuple(h.solid for h in HOOKS)), color='#4d9d7a',
    refs=[('board', 'HC-SR501', hc_sr501(at=BOARD))], boards=(Mount(PCB, 'board', HOOKS),),
    notes=['Bo 32×24 mm, thấu kính Ø23; chiều cao các trang bán hàng ghi 18 đến 30 mm không khớp nhau, hãy đo.',
           'Mặt +z là cửa sổ cho thấu kính nên không có điểm nối.',
           'Bo treo vào bốn trụ từ trần, hai móc gài ở hai cạnh dài giữ mặt dưới PCB: đẩy bo lên là móc bật vào; lắp từ phía nắp −z rồi đóng nắp.'])
