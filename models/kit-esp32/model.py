"""Module ESP32-C3 mini: 2 x 2 x 2 units. ESP32-C3 SuperMini on four posts, USB-C at mid height. Millimetres, Z up."""
import itertools

from printkit.library.electronics import esp32_c3_supermini
from printkit.modules import WALL, ModuleSpec, bounds, box, cyl, kit_model

CELLS = (2, 2, 2)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX = (LO[0] + HI[0]) / 2
FLOOR = LO[2] + WALL
BOARD_Z = (LO[2] + HI[2]) / 2 - 3.2                  # USB-C axis at mid height, in the channel between the two connector rows
BOARD_Y = LO[1] + WALL + 0.5 + 12.75                 # PCB front 0.5 mm from the -y wall, USB overhang 1.5 mm
USB_SLOT = box((CX - 6, 0, BOARD_Z + 0.2), (CX + 6, LO[1] + WALL + 1, BOARD_Z + 6.2))
POSTS = tuple(cyl((CX + sx, BOARD_Y + sy, FLOOR - 0.5), (0, 0, 1), 1.5, BOARD_Z - FLOOR + 0.5)
              for sx, sy in itertools.product((-4.6, 4.6), (-7.4, 7.4)))

model = kit_model(
    'kit-esp32', title='Module ESP32-C3 mini',
    description='Bo ESP32-C3 SuperMini trong khối 2×2×2, cổng USB-C ở mặt trước.',
    spec=ModuleSpec(cells=CELLS, lid='+y', cuts=(USB_SLOT,), adds=POSTS), color='#367c85',
    refs=[('board', 'ESP32-C3 SuperMini', esp32_c3_supermini(at=(CX, BOARD_Y, BOARD_Z)))],
    notes=['Bốn trụ đỡ mặt dưới PCB; bo cần cố định thêm bằng keo hoặc băng dính.',
           'Khe USB-C nằm trong dải giữa hai hàng lỗ khoét ở mặt −y, nên không cắt vào lỗ nào.'])
