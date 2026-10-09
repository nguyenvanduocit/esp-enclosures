"""Module cảm biến MPU6050: 2 x 2 x 1 units. GY-521 board on four posts, lid on top. Millimetres, Z up."""
import itertools

from printkit.library.electronics import mpu6050
from printkit.modules import WALL, ModuleSpec, bounds, cyl, kit_model

CELLS = (2, 2, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+z'))
CX, CY = (LO[0] + HI[0]) / 2, (LO[1] + HI[1]) / 2
FLOOR = LO[2] + WALL
BOARD = (CX, CY, 6.0)                                  # PCB underside; the header body (2.5 mm) hangs under it
# four Ø2.4 posts from the floor; each top face touches the PCB underside
POSTS = tuple(cyl((CX + sx, CY + sy, FLOOR - 0.5), (0, 0, 1), 1.2, BOARD[2] - FLOOR + 0.5)
              for sx, sy in itertools.product((-8, 8), (-2, 2)))

model = kit_model(
    'kit-mpu6050', title='Module cảm biến MPU6050',
    description='Cảm biến gia tốc và con quay GY-521 MPU6050 trong khối 2×2×1.',
    spec=ModuleSpec(cells=CELLS, lid='+z', adds=POSTS), color='#d06a6a',
    refs=[('board', 'GY-521 MPU6050', mpu6050(at=BOARD))],
    notes=['Bo khoảng 20,5×16 mm theo trang bán hàng, các nơi ghi 20×16 đến 21×16,4; đo bo của bạn.',
           'Hàng chân cắm nằm gần cạnh −y của bo, dọc theo chiều dài bo (trục x của mô hình); mô hình không đánh dấu trục của chip.',
           'Hàn dây trực tiếp hoặc dùng dải chân cắm ngắn: từ đỉnh chip tới tấm nắp còn 9,4 mm.'])
