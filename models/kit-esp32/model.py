"""Module ESP32-C3 mini: 2 x 2 x 2 units. ESP32-C3 SuperMini on four posts, held by two snap hooks, USB-C at mid height. Millimetres, Z up."""
import itertools

from printkit.library.electronics import SUPERMINI_PCB, esp32_c3_supermini
from printkit.modules import WALL, ModuleSpec, Mount, Pcb, bounds, box, corner_stop, cyl, edge_stop, kit_model, snap_hook

CELLS = (2, 2, 2)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX = (LO[0] + HI[0]) / 2
FLOOR = LO[2] + WALL
BOARD_Z = (LO[2] + HI[2]) / 2 - 3.2                  # USB-C axis at mid height, in the channel between the two connector rows
BOARD_Y = LO[1] + WALL + 0.5 + 12.75                 # USB front 0.5 mm from the -y wall (PCB front 2.0 mm), USB overhang 1.5 mm
USB_SLOT = box((CX - 6, 0, BOARD_Z + 0.2), (CX + 6, LO[1] + WALL + 1, BOARD_Z + 6.2))
POSTS = tuple(cyl((CX + sx, BOARD_Y + sy, FLOOR - 0.5), (0, 0, 1), 1.5, BOARD_Z - FLOOR + 0.5)
              for sx, sy in itertools.product((-4.6, 4.6), (-7.4, 7.4)))
PCB = Pcb((CX, BOARD_Y, BOARD_Z), SUPERMINI_PCB)
# two beams from the -y wall along the +-x edges, barbs over the PCB top at mid length; the -y wall lies on the bed, so the beams print upright
HOOKS = tuple(snap_hook(PCB, side, root=('y', LO[1] + WALL)) for side in ('+x', '-x'))
# In-plane stops: two blocks on the -y wall, one each side of the USB slot, and two corner stops held out from the +-x walls
# past the PCB's +y edge; each stops the board 0.2 mm away, and all print upright from the -y wall.
FRONT = tuple(edge_stop(PCB, '-y', root=('y', LO[1] + WALL), span=span) for span in ((CX - 8.8, CX - 6.2), (CX + 6.2, CX + 8.8)))
BACK = tuple(corner_stop(PCB, '+y', wall=wall) for wall in (LO[0] + WALL, HI[0] - WALL))

model = kit_model(
    'kit-esp32', title='Module ESP32-C3 mini',
    description='Bo ESP32-C3 SuperMini trong khối 2×2×2, cổng USB-C ở mặt trước.',
    spec=ModuleSpec(cells=CELLS, lid='+y', cuts=(USB_SLOT,), adds=POSTS + tuple(h.solid for h in HOOKS) + FRONT + BACK), color='#367c85',
    refs=[('board', 'ESP32-C3 SuperMini', esp32_c3_supermini(at=(CX, BOARD_Y, BOARD_Z)))], boards=(Mount(PCB, 'board', HOOKS),),
    notes=['Bốn trụ đỡ mặt dưới PCB, hai móc gài ở hai cạnh dọc giữ mặt trên: ấn bo xuống là móc bật vào, không cần keo.',
           'Khe USB-C nằm trong dải giữa hai hàng lỗ khoét ở mặt −y, nên không cắt vào lỗ nào.'])
