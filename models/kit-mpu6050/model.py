"""Module cảm biến MPU6050: 2 x 2 x 1 units. GY-521 board on four posts, held by two snap hooks, lid on top. Millimetres, Z up."""
import itertools

from printkit.library.electronics import MPU6050_PCB, mpu6050
from printkit.modules import WALL, ModuleSpec, Mount, Pcb, bounds, cyl, edge_stop, kit_model, snap_hook

CELLS = (2, 2, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+z'))
CX, CY = (LO[0] + HI[0]) / 2, (LO[1] + HI[1]) / 2
FLOOR = LO[2] + WALL
# PCB underside. The header body (2.5 mm) and its pins (8.5 mm below the underside) hang under it: at this height the pin
# tips stay 0.6 mm above the floor and the pin tops 3.7 mm under the lid plate; the 1.0 mm hook stems bend over 10.3 mm.
BOARD = (CX, CY, 11.2)
STEM_T = 1.0
# four Ø2.4 posts from the floor; each top face touches the PCB underside
POSTS = tuple(cyl((CX + sx, CY + sy, FLOOR - 0.5), (0, 0, 1), 1.2, BOARD[2] - FLOOR + 0.5)
              for sx, sy in itertools.product((-8, 8), (-2, 2)))
PCB = Pcb(BOARD, MPU6050_PCB)  # listings give 20 x 16 to 21 x 16.4; the check proves 20.2 to 20.8 x 15.7 to 16.3 (±0.3)
# two stems from the floor at the +-x edges, in the floor band between the washer pockets
HOOKS = tuple(snap_hook(PCB, side, root=('z', FLOOR), thickness=STEM_T) for side in ('+x', '-x'))
# two blocks on the floor stop the board 0.2 mm past its +-y edges, in the same floor band
STOPS = tuple(edge_stop(PCB, side, root=('z', FLOOR), span=(CX - 2, CX + 2)) for side in ('+y', '-y'))

model = kit_model(
    'kit-mpu6050', title='Module cảm biến MPU6050',
    description='Cảm biến gia tốc và con quay GY-521 MPU6050 trong khối 2×2×1.',
    spec=ModuleSpec(cells=CELLS, lid='+z', adds=POSTS + tuple(h.solid for h in HOOKS) + STOPS), color='#d06a6a',
    refs=[('board', 'GY-521 MPU6050', mpu6050(at=BOARD))], boards=(Mount(PCB, 'board', HOOKS),),
    notes=['Bo khoảng 20,5×16 mm theo trang bán hàng, các nơi ghi 20×16 đến 21×16,4; đo bo của bạn.',
           'Hàng chân cắm nằm gần cạnh −y của bo, dọc theo chiều dài bo (trục x của mô hình); mô hình không đánh dấu trục của chip.',
           'Hàng chân cắm hàn chân dài xuống dưới: đầu chân cách sàn 0,6 mm, đầu chân phía trên cách tấm nắp 3,7 mm.',
           'Bốn trụ đỡ mặt dưới PCB, hai móc gài ở hai cạnh ngắn giữ mặt trên: ấn bo xuống là móc bật vào, không cần keo.'])
