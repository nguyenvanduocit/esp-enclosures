"""Module cảm biến PIR: 2 x 2 x 2 units. HC-SR501 hangs from the ceiling, its lens passes through a hole in the +z face. Millimetres, Z up."""
import itertools

from printkit.library.electronics import hc_sr501
from printkit.modules import WALL, ModuleSpec, bounds, cyl, kit_model

CELLS = (2, 2, 2)
LO, HI = bounds(ModuleSpec(CELLS, '-z'))
CX, CY = (LO[0] + HI[0]) / 2, (LO[1] + HI[1]) / 2
LENS_TOP = HI[2] - 0.9                                 # the lens ends 0.9 mm under the outer top face
BOARD = (CX, CY, LENS_TOP - 19.2)                      # PCB underside; PCB 1.2 thick plus 18 mm lens
CEILING = HI[2] - WALL
HOLE = cyl((CX, CY, HI[2] - WALL - 1), (0, 0, 1), 12.2, WALL + 2)          # O24.4 for the O23 lens
HANGERS = tuple(cyl((CX + sx, CY + sy, BOARD[2] + 1.2), (0, 0, 1), 1.5, CEILING + 0.5 - (BOARD[2] + 1.2))
                for sx, sy in itertools.product((-13, 13), (-9, 9)))

model = kit_model(
    'kit-pir', title='Module cảm biến PIR',
    description='Cảm biến chuyển động HC-SR501, thấu kính nhô qua lỗ ở mặt trên, khối 2×2×2.',
    spec=ModuleSpec(cells=CELLS, lid='-z', plain=('+z',), cuts=(HOLE,), adds=HANGERS), color='#4d9d7a',
    refs=[('board', 'HC-SR501', hc_sr501(at=BOARD))],
    notes=['Bo 32×24 mm, thấu kính Ø23; chiều cao các trang bán hàng ghi 18 đến 30 mm không khớp nhau, hãy đo.',
           'Mặt +z là cửa sổ cho thấu kính nên không có điểm nối.',
           'Bo treo vào bốn trụ từ trần; lắp từ phía nắp −z rồi đóng nắp.'])
