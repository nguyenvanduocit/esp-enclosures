"""Module pin 18650 + sạc: 3 x 4 x 2 units. 18650 holder against -x, TP4056 USB-C charger on four posts beside it. Millimetres, Z up."""
import itertools

import cadquery as cq

from printkit import Box, Solid
from printkit.library.electronics import tp4056_usbc
from printkit.modules import WALL, ModuleSpec, bounds, box, cyl, kit_model

CELLS = (3, 4, 2)
LO, HI = bounds(ModuleSpec(CELLS, '+x'))
FLOOR = LO[2] + WALL
HOLDER = (22, 75, 18)                                 # open single 18650 holder, 75 x 22 x 18 per listings
HOLDER_X = LO[0] + WALL + 0.8 + HOLDER[0] / 2          # 0.8 mm against the -x wall for adhesive
HOLDER_Z = FLOOR + 0.8
CELL_Z = HOLDER_Z + 10.3
CY = (LO[1] + HI[1]) / 2
CHARGER = (36.0, 17.5, 16.75)                          # PCB underside centre; the USB-C axis ends at z = 20, mid height
CHARGER_POSTS = tuple(cyl((CHARGER[0] + sx, CHARGER[1] + sy, FLOOR - 0.5), (0, 0, 1), 1.5, CHARGER[2] - FLOOR + 0.5)
                      for sx, sy in itertools.product((-6, 6), (-10, 10)))
USB_SLOT = box((CHARGER[0] - 5.2, 0, 17.7), (CHARGER[0] + 5.2, LO[1] + WALL + 1, 22.3))

cell = cq.Workplane('XY').add(cq.Solid.makeCylinder(9.25, 65.3, cq.Vector(HOLDER_X, CY - 32.65, CELL_Z), cq.Vector(0, 1, 0)))

model = kit_model(
    'kit-battery', title='Module pin 18650 + sạc',
    description='Một viên 18650 trong khay hở cùng mạch sạc TP4056 USB-C, khối 3×4×2.',
    spec=ModuleSpec(cells=CELLS, lid='+x', cuts=(USB_SLOT,), adds=CHARGER_POSTS), color='#5f8f5b',
    refs=[('holder', 'Khay pin 18650', [Box('holder', HOLDER, (HOLDER_X, CY, HOLDER_Z + HOLDER[2] / 2), '#303d46')]),
          ('cell', 'Pin 18650', [Solid('cell', cell, '#87b483')]),
          ('charger', 'Mạch sạc TP4056 USB-C', tp4056_usbc(at=CHARGER))],
    notes=['Khoảng trống trong chiều dài là 75,8 mm cho khay 75 mm: chỉ còn 0,4 mm, hãy đo khay thật.',
           'Mạch sạc đặt trên bốn trụ; cổng USB-C nhìn ra khe ở mặt −y, nằm giữa hai hàng lỗ khoét.',
           'Không có mạch tăng áp; bạn tự chọn cách nối pin với ESP32-C3 SuperMini.',
           'Thay pin bằng cách mở nắp ở mặt +x.'])
