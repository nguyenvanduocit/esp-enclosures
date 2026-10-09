"""Module cảm biến BME280: 1 x 1 x 1 unit. GY-BME280 board slides along -y in two grooves on the +-x walls; the closed lid stops it
sliding out. The -y face is plain with vent slots. Millimetres, Z up."""
from printkit import Box
from printkit.library.electronics import bme280
from printkit.modules import HOOK_GAP, HOOK_SIDE_GAP, HOOK_T, SLIDE_RAILS, WALL, ModuleSpec, Pcb, bounds, box, edge_lip, kit_model

CELLS = (1, 1, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX, CZ = (LO[0] + HI[0]) / 2, (LO[2] + HI[2]) / 2
# PCB underside centre; PCB spans y 3.3 to 14.9, below the lid skirt band (y >= 15.5). The underside sits at 14.0 so both grooves
# (z 12.8 to 17.0) stay above the Ø5 ports of the +-x walls (z 7.5 to 12.5).
BOARD = (CX, 9.1, 14.0)
# three 1.6 mm wide slots through the -y wall, 9 mm tall, 4 mm apart
VENTS = tuple(box((CX + dx - 0.8, 0, CZ - 4.5), (CX + dx + 0.8, LO[1] + WALL + 0.5, CZ + 4.5)) for dx in (-4, 0, 4))
PCB = Pcb(BOARD, (15.4, 11.6, 1.6), retention=SLIDE_RAILS)
UNDER = PCB._replace(held=-1)
# Each groove is a rail over the PCB top along the whole board and a ledge under it up to y 11.0. Both grow from the -y wall, which
# lies on the bed, so they print upright. The header under the board rides at its +y end (y 11.35 to 13.85) and never crosses a ledge.
RAIL_END, LEDGE_END = 15.3, 11.0
GROOVES = tuple(part for side, wall in (('+x', HI[0] - WALL), ('-x', LO[0] + WALL))
                for part in (edge_lip(PCB, side, wall=wall, span=(LO[1] + WALL - 0.2, RAIL_END)),
                             edge_lip(UNDER, side, wall=wall, span=(LO[1] + WALL - 0.2, LEDGE_END), gap=0)))
# Two end stops at the -y corners, the full groove height, stop the board HOOK_SIDE_GAP before the -y wall, so it slides 0.2 mm
# towards the wall and 0.6 mm towards the closed lid; without them the header under the board would hit the ledge ends first.
PCB_LO = (BOARD[0] - PCB.size[0] / 2, BOARD[1] - PCB.size[1] / 2)
Z0, Z1 = BOARD[2] - HOOK_T, BOARD[2] + PCB.size[2] + HOOK_GAP + HOOK_T
STOPS = tuple(box((x0, LO[1] + WALL - 0.2, Z0), (x1, PCB_LO[1] - HOOK_SIDE_GAP, Z1))
              for x0, x1 in ((LO[0] + WALL - 0.2, PCB_LO[0] + 0.6), (PCB_LO[0] + PCB.size[0] - 0.6, HI[0] - WALL + 0.2)))


def turned(pieces):
    """The board turned 180° about its vertical axis, so its header sits at the +y end."""
    return [Box(p.name, p.size, (2 * BOARD[0] - p.center[0], 2 * BOARD[1] - p.center[1], p.center[2]), p.color) for p in pieces]


model = kit_model(
    'kit-bme280', title='Module cảm biến BME280',
    description='Cảm biến nhiệt độ, độ ẩm, áp suất GY-BME280 trong khối 1×1×1, mặt trước có khe thoáng.',
    spec=ModuleSpec(cells=CELLS, lid='+y', plain=('-y',), cuts=VENTS, adds=GROOVES + STOPS), color='#c9884a',
    refs=[('board', 'GY-BME280', turned(bme280(at=BOARD)))], boards=(PCB,),
    notes=['Chiều rộng trong 15,8 mm cho bo 15,4 mm: chỉ còn 0,4 mm cho cả hai bên (0,2 mm mỗi bên). Hãy đo bo của bạn, nếu lớn hơn thì cần khối 2×1×1.',
           'Bo trượt vào hai rãnh ở hai thành ±x, hàng chân cắm ở phía nắp; nắp đóng lại chặn bo không trượt ra. Bo không có tiếng tách khi vào.',
           'Dưới đầu cắm còn 9,4 mm tới sàn, chưa đủ cho đầu Dupont: hàn dây trực tiếp vào bo.',
           'Mặt −y trơn có ba khe thoáng để cảm biến đo không khí ngoài.'])
