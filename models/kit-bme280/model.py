"""Module cảm biến BME280: 1 x 1 x 1 unit. GY-BME280 board on two ribs; the -y face is plain with vent slots. Millimetres, Z up."""
from printkit.library.electronics import bme280
from printkit.modules import WALL, ModuleSpec, bounds, box, cyl, kit_model

CELLS = (1, 1, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX, CZ = (LO[0] + HI[0]) / 2, (LO[2] + HI[2]) / 2
BOARD = (CX, 9.1, CZ - 1.2)                            # PCB underside centre; PCB spans y 3.3 to 14.9, below the lid skirt band (y >= 15.5)
# three 1.6 mm wide slots through the -y wall, 9 mm tall, 4 mm apart
VENTS = tuple(box((CX + dx - 0.8, 0, CZ - 4.5), (CX + dx + 0.8, LO[1] + WALL + 0.5, CZ + 4.5)) for dx in (-4, 0, 4))
# two Ø2.4 ribs from the floor; each top face touches the PCB underside
RIBS = tuple(cyl((CX + dx, 11.5, LO[2] + WALL - 0.5), (0, 0, 1), 1.2, BOARD[2] - (LO[2] + WALL) + 0.5) for dx in (-5.5, 5.5))

model = kit_model(
    'kit-bme280', title='Module cảm biến BME280',
    description='Cảm biến nhiệt độ, độ ẩm, áp suất GY-BME280 trong khối 1×1×1, mặt trước có khe thoáng.',
    spec=ModuleSpec(cells=CELLS, lid='+y', plain=('-y',), cuts=VENTS, adds=RIBS), color='#c9884a',
    refs=[('board', 'GY-BME280', bme280(at=BOARD))],
    notes=['Chiều rộng trong 15,8 mm cho bo 15,4 mm: chỉ còn 0,4 mm cho cả hai bên (0,2 mm mỗi bên). Hãy đo bo của bạn, nếu lớn hơn thì cần khối 2×1×1.',
           'Dưới đầu cắm chỉ còn 4,2 mm tới sàn, không đủ cho đầu Dupont: hàn dây trực tiếp vào bo.',
           'Mặt −y trơn có ba khe thoáng để cảm biến đo không khí ngoài.'])
