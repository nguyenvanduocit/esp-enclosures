"""Module màn hình 2.4": 4 x 3 x 1 units. ILI9341 board under a 49 x 37 window in the +z face. Millimetres, Z up."""
from printkit.library.electronics import ili9341_24
from printkit.modules import WALL, ModuleSpec, bounds, box, kit_model

CELLS = (4, 3, 1)
LO, HI = bounds(ModuleSpec(CELLS, '+y'))
CX = (LO[0] + HI[0]) / 2
PY = LO[1] + WALL + 0.8 + 43.3 / 2                    # PCB 0.8 mm from the -y wall
GLASS_TOP = HI[2] - WALL - 0.2                        # glass sits 0.2 mm under the plain top wall
PCB_Z = GLASS_TOP - 3.2 - 1.6                         # PCB underside
WINDOW = box((CX - 24.48, PY - 18.36, HI[2] - WALL - 1), (CX + 24.48, PY + 18.36, HI[2] + 1))   # active area 48.96 x 36.72

model = kit_model(
    'kit-display', title='Module màn hình 2.4"',
    description='Màn hình TFT 2.4" ILI9341 dưới khung hiển thị 49×37 mm, khối 4×3×1.',
    spec=ModuleSpec(cells=CELLS, lid='+y', plain=('+z',), cuts=(WINDOW,)), color='#7b6cd9',
    refs=[('display', 'Màn hình ILI9341 2.4"', ili9341_24(at=(CX, PY, PCB_Z)))],
    notes=['Mặt +z là màn hình nên không có điểm nối.',
           'Cửa sổ 49×37 mm theo vùng hiển thị 48,96×36,72 mm; kính 60×40 mm là giả định, hãy đo màn hình của bạn.',
           'Bo lắp từ phía nắp +y rồi trượt vào dưới khung.'])
