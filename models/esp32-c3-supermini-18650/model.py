"""ESP32-C3 SuperMini + removable 18650 + TPS63020 module. Millimetres, Z up.

Hardware envelopes are assumptions; see README before printing.
"""
from functools import cache

import cadquery as cq

from printkit import Box, Drag, Model, Solid, dim
from printkit.checks import CheckFailed, clear
from printkit.library.electronics import SUPERMINI_PCB, esp32_c3_supermini
from printkit.shapes import block, box_solid, rounded

W, L, FLOOR, WALL, BASE_H, CAP_T = 60.0, 84.0, 2.0, 2.0, 25.4, 1.8
HEIGHT = BASE_H + CAP_T
DIVIDER_X = -1.5
ESP_X, ESP_Y, ESP_Z = 14.0, -26.5, 12.0
CELL_X, CELL_Z, CELL_D, CELL_L = -16.5, 13.1, 18.5, 65.3
HOLDER_W, HOLDER_L, HOLDER_H, HOLDER_Z = 22.0, 75.0, 18.0, 2.8
MOD_X, MOD_Y, MOD_Z, MOD_W, MOD_L, MOD_H = 14.0, 14.0, 6.0, 24.0, 34.0, 4.5
FIT, SKIRT_H, EPS = .2, 2.4, .02
USB_BOTTOM, USB_W = ESP_Z - .8, 14.0
USB_CAP_FACE_T, USB_CAP_DEPTH = 1.2, 1.7
USB_CAP_CENTER_Z = (USB_BOTTOM + BASE_H) / 2
USB_CAP_FRONT_Y = -L / 2 - USB_CAP_FACE_T
LIDS = {
    'battery_lid': {'cavity_center': -15.25, 'cavity_width': 25.5},
    'electronics_lid': {'cavity_center': 13.75, 'cavity_width': 28.5},
}
PCB_W, PCB_L, PCB_T = SUPERMINI_PCB
BOARD = esp32_c3_supermini(at=(ESP_X, ESP_Y, ESP_Z))
CONVERTER = [Box('module_pcb', (24, 34, 1), (14, 14, 6.5), '#27729a'),
             Box('inductor', (7, 7, 3.5), (14, 13, 8.75), '#485760'),
             Box('regulator', (4, 4, 1.2), (14, 22, 7.6), '#202c34')]
CONVERTER += [Box(f'pad_{x}_{y}', (3, 4, .1), (x, y, 7.05), '#cba35e') for x in (5, 23) for y in (1, 27)]

PRINT_INFO = {'summary': '≈ 40–50 g PLA · chưa in thử', 'sections': [
    {'title': 'Cấu hình in thử',
     'rows': [['Máy / vật liệu', 'Chọn đúng máy · nozzle 0,4 mm · PLA thường'],
              ['Layer / lớp đầu', '0,16 / 0,20 mm'], ['Thành', 'Arachne · 3 wall loops'],
              ['Lớp đặc trên / dưới', '5 / 5'], ['Infill', '15% Gyroid'],
              ['Thành ngoài / cầu', '60 / 25 mm/s'], ['Support / brim', 'Tắt ban đầu'],
              ['Scale / đơn vị', '100% / mm'], ['Bù lỗ / biên XY', '0 / 0 mm'],
              ['Nhiệt, quạt, flow, bù chân voi', 'Theo preset nhựa và bàn in']],
     'notes': ['Arachne hỗ trợ gờ mỏng; kiểm tra đường nhựa sau khi Slice. Không scale hộp để chỉnh độ chặt ngàm.',
               'Thân: đáy xuống bàn, miệng hướng lên.',
               'Nắp và nút USB: mặt ngoài xuống bàn, phần gài hướng lên.',
               'Xem cầu 8 mm ở cửa dây, Z ≈ 10 mm, và rãnh nắp pin rộng 1,2 mm, sâu 0,4 mm. Chỉ thêm support cục bộ nếu cầu thử bị võng.',
               'Nếu nắp cong góc: thêm outer brim 3–5 mm.'],
     'links': [{'label': 'Arachne', 'url': 'https://wiki.bambulab.com/en/software/bambu-studio/wall-generator'},
               {'label': 'Bù chân voi', 'url': 'https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot'}]},
    {'title': 'Nhựa & chi phí',
     'rows': [['Thân', '34,6 g'], ['Nắp pin', '6,0 g'], ['Nắp mạch', '6,5 g'], ['Nút USB', '0,8 g'],
              ['Tổng nếu in đặc', '47,9 g']],
     'notes': ['Tính từ thể tích CAD với PLA 1,24 g/cm³. Infill giảm phần ruột; brim và nhựa mồi cộng thêm.',
               'Ví dụ cuộn 300.000đ/kg: khoảng 12.000–15.000đ/bộ, chưa tính điện và in lỗi. Bambu Studio cho số ước tính theo cấu hình sau khi Slice.'],
     'links': [{'label': 'PLA 1,24 g/cm³', 'url': 'https://store.bblcdn.com/s7/default/b189de92249a4b9ebed28b8ea1f080f0/Bambu_PLA_Basic_Technical_Data_Sheet.pdf'}]},
    {'title': 'Độ vừa', 'rows': [],
     'notes': ['4 STL kín, mỗi file một khối.',
               'Không cạnh/đỉnh lỗi, mặt tự giao, mặt trùng hoặc tam giác suy biến; hướng mặt nhất quán.',
               'Thành/đáy 2 mm; nắp 1,8 mm; gờ nhỏ nhất 1 mm. Kiểm tra gờ và gân cài còn đủ trong Preview.',
               'Mép cài nắp 1,2 mm, sâu 2,4 mm. Khe hở 0,2 mm mỗi bên; gân dôi 0,08 mm. In thử để chỉnh độ chặt.',
               'Nút USB sâu 1,7 mm, cách cổng trên bo 1,05 mm theo model; không có gioăng kín nước.',
               'Đo khay, pin và module thực trước khi in. Linh kiện trên bo là hình minh họa; chưa chừa giắc Dupont.',
               'Khay và bo cần cố định thêm. Cửa dây 8 × 6 mm; chưa có rãnh hoặc kẹp dây.'],
     'links': []}]}

model = Model(
    'esp32-c3-supermini-18650', title='ESP32-C3 + 18650',
    description='Pin tháo rời, hai nắp độc lập và nút bịt USB.',
    category='Hộp điện tử', status='Chưa in thử', thumbnail='thumbnail.png',
    dimensions=(W, L + USB_CAP_FACE_T, HEIGHT),
    camera={'position': [145, -196, 158], 'target': [0, 0, 16], 'minDistance': 55, 'maxDistance': 550,
            'views': [{'id': 'front', 'label': 'Trước', 'offset': [0, -285, 0.01]},
                      {'id': 'top', 'label': 'Trên', 'offset': [0, -0.01, 285]}]},
    grid={'size': 180, 'divisions': 36}, print_info=PRINT_INFO)


@model.part('base', 'Thân', color='#367c85', drag=Drag((0, 0, -1), 60))
def base():
    shell = rounded(W, L, BASE_H, 4).cut(rounded(W - 2 * WALL, L - 2 * WALL, BASE_H, 2, z=FLOOR))
    divider = block(2, L - 2 * WALL + EPS, BASE_H, x=DIVIDER_X)
    divider = divider.cut(block(4, 8, 6, x=DIVIDER_X, y=-8, z=4))
    shell = shell.union(divider)
    # Four supports lie inside the header rows. No board mounting holes assumed.
    for x in (-4.6, 4.6):
        for y in (-7.4, 7.4):
            post = cq.Workplane('XY').circle(1.5).extrude(ESP_Z)
            shell = shell.union(post.translate((ESP_X + x, ESP_Y + y, 0)))
    for x in (-10.35, 10.35):
        for y in (-6.1, 6.1):
            shell = shell.union(block(2.2, 2.2, ESP_Z + 1.6, ESP_X + x, ESP_Y + y))
    shell = shell.union(block(8, 2, ESP_Z + 1.6, ESP_X, ESP_Y + 12.55))
    for x in (-6.8, 6.8):
        shell = shell.union(block(2.8, 2, ESP_Z + 1.6, ESP_X + x, ESP_Y - 12.55))
    # Holder envelope 75 x 22 x 18; adhesive allowance below it is 0.8 mm.
    for y in (-38.3, 38.3):
        shell = shell.union(block(16, 1, 6, CELL_X, y))
    for y in (-26, 26):
        shell = shell.union(block(1, 10, 6, -4.7, y))
    # TPS63020 supports plus 0.5 mm adhesive; reserve 35 x 24 mm footprint.
    for x in (5, 23):
        shell = shell.union(block(2.2, 30, 5.5, x, 14))
    for x in (1.2, 26.8):
        for y in (3, 25):
            shell = shell.union(block(1, 5, 8, x, y))
    for y in (-4.1, 32.1):
        shell = shell.union(block(12, 1, 8, 14, y))
    shell = shell.cut(block(USB_W, 10, BASE_H, ESP_X, -L / 2, USB_BOTTOM))
    # Fingernail recess under the removable battery cover.
    shell = shell.cut(block(8, 4, 1.1, CELL_X, -L / 2, BASE_H - 1))
    return shell.clean()


@cache
def installed_lid(name, ribs=True):
    spec = LIDS[name]
    plate = rounded(W, L, CAP_T, 4, z=BASE_H)
    if name == 'battery_lid':
        plate = plate.intersect(block(100, 100, 50, x=-51.6))
    else:
        plate = plate.intersect(block(100, 100, 50, x=48.6))
    cx, cw = spec['cavity_center'], spec['cavity_width']
    skirt = rounded(cw - 2 * FIT, 80 - 2 * FIT, SKIRT_H + EPS, 1.6, x=cx, z=BASE_H - SKIRT_H)
    skirt = skirt.cut(rounded(cw - 2 * (FIT + 1.2), 80 - 2 * (FIT + 1.2), SKIRT_H + 3 * EPS,
                              .5, x=cx, z=BASE_H - SKIRT_H - EPS))
    if name == 'electronics_lid':
        skirt = skirt.cut(block(14.6, 6, SKIRT_H + EPS, ESP_X, -40, BASE_H - SKIRT_H))
        for y in (20, 23, 26):
            vent = cq.Workplane('XY').slot2D(12, 1.4).extrude(CAP_T + 2 * EPS)
            plate = plate.cut(vent.translate((14, y, BASE_H - EPS)))
    else:
        # Shallow tactile grooves, no through openings above the cell.
        for y in (-28, -25, -22):
            plate = plate.cut(block(12, 1.2, .5, CELL_X, y, HEIGHT - .4))
    lid = plate.union(skirt)
    if ribs:
        for side in (-1, 1):
            for y in (-24, 24):
                rib = cq.Workplane('XY').circle(.35).extrude(SKIRT_H + EPS)
                lid = lid.union(rib.translate((cx + side * (cw / 2 - .27), y, BASE_H - SKIRT_H)))
    return lid.clean()


@model.part('batteryLid', 'Nắp pin', color='#c9dba7', drag=Drag((0, 0, 1), 100), print_rotation=(0, 180, 0))
def battery_lid():
    return installed_lid('battery_lid')


@model.part('electronicsLid', 'Nắp mạch', color='#ded4ba', drag=Drag((0, 0, 1), 100), print_rotation=(0, 180, 0))
def electronics_lid():
    return installed_lid('electronics_lid')


@cache
def installed_usb_cap(ribs=True):
    """Removable cover gripping the enclosure opening, clear of the USB socket."""
    opening_h = BASE_H - USB_BOTTOM
    face = block(USB_W + 3, USB_CAP_FACE_T, opening_h + 3,
                 ESP_X, -L / 2 - USB_CAP_FACE_T / 2, USB_BOTTOM - 1.5).edges('|Y').fillet(.8)
    tongue = block(USB_W - 2 * FIT, USB_CAP_DEPTH + EPS, opening_h - 2 * FIT,
                   ESP_X, -L / 2 + (USB_CAP_DEPTH - EPS) / 2, USB_BOTTOM + FIT).edges('|Y').fillet(.5)
    cap = face.union(tongue)
    if ribs:
        for side in (-1, 1):
            for z in (USB_CAP_CENTER_Z - 3, USB_CAP_CENTER_Z + 3):
                rib = cq.Workplane('XY').circle(.28).extrude(1.2 + EPS)
                rib = rib.rotate((0, 0, 0), (1, 0, 0), -90)
                cap = cap.union(rib.translate((ESP_X + side * (USB_W / 2 - FIT), -L / 2 - EPS, z)))
    return cap.clean()


@model.part('usbCap', 'Bịt USB', color='#e4ab64', drag=Drag((0, -1, 0), 60), print_rotation=(90, 0, 0))
def usb_cap():
    return installed_usb_cap()


def holder_shape():
    holder = block(HOLDER_W, HOLDER_L, 1, CELL_X, z=HOLDER_Z)
    for x in (-10.45, 10.45):
        holder = holder.union(block(1.1, HOLDER_L, 8, CELL_X + x, z=HOLDER_Z))
    for y in (-35.75, 35.75):
        holder = holder.union(block(HOLDER_W, 3.5, HOLDER_H, CELL_X, y, HOLDER_Z))
    return holder


def cell_shape():
    cell = cq.Workplane('XY').circle(CELL_D / 2).extrude(CELL_L)
    return cell.rotate((0, 0, 0), (1, 0, 0), 90).translate((CELL_X, CELL_L / 2, CELL_Z))


HOLDER, CELL = holder_shape(), cell_shape()
model.reference('board', 'ESP32', BOARD, drag=Drag((0, 0, 1), 90))
model.reference('cell', 'Pin', [Solid('cell', CELL, '#87b483')], drag=Drag((0, 0, 1), 90))
model.reference('holder', 'Khay', [Solid('holder', HOLDER, '#303d46')], drag=Drag((0, 0, 1), 90))
model.reference('converter', 'Mạch nguồn', CONVERTER, drag=Drag((0, 0, 1), 90))


def pulse(value):
    rest = (0, 0, 0)
    return [(0, rest), (0.08, rest), (0.4, value), (0.72, value), (0.97, rest), (1, rest)]


def case_lines(front_y):
    return [
        dim((-W / 2, -L / 2, 0), (W / 2, -L / 2, 0), (0, -8, 0), 'Rộng', (0, -4.8, 0)),
        dim((W / 2, front_y, 0), (W / 2, L / 2, 0), (8, 0, 0), 'Dài', (9.6, 0, 0)),
        dim((-W / 2, -L / 2, 0), (-W / 2, -L / 2, HEIGHT), (-8, 0, 0), 'Cao vỏ', (-11.2, 0, 0)),
    ]


def footprint(x0, x1, y0, y1, z0, z1, names):
    """Width, length and height lines around a component envelope."""
    width, length, height = names
    return [dim((x0, y0, z1), (x1, y0, z1), (0, -5, 0), width, (0, -5, 2)),
            dim((x1, y0, z1), (x1, y1, z1), (5, 0, 0), length, (13, 0, 3)),
            dim((x0, y1, z0), (x0, y1, z1), (-5, 0, 0), height, (-14, 0, 3))]


model.measure('case', 'Vỏ hộp', kind='case', follow='base',
              lines=case_lines(USB_CAP_FRONT_Y), variants={'usbCap': case_lines(-L / 2)})
model.measure('board', 'PCB ESP32', kind='component', follow='board', visible_with='board',
              lines=footprint(ESP_X - PCB_W / 2, ESP_X + PCB_W / 2, ESP_Y - PCB_L / 2, ESP_Y + PCB_L / 2,
                              ESP_Z, ESP_Z + PCB_T, ('PCB rộng', 'PCB dài', 'PCB dày')))
model.measure('holder', 'Khay', kind='component', follow='holder', visible_with='holder',
              lines=footprint(CELL_X - HOLDER_W / 2, CELL_X + HOLDER_W / 2, -HOLDER_L / 2, HOLDER_L / 2,
                              HOLDER_Z, HOLDER_Z + HOLDER_H, ('Khay rộng', 'Khay dài', 'Khay cao')))
model.measure('converter', 'Mạch nguồn', kind='component', follow='converter', visible_with='converter',
              lines=footprint(MOD_X - MOD_W / 2, MOD_X + MOD_W / 2, MOD_Y - MOD_L / 2, MOD_Y + MOD_L / 2,
                              MOD_Z, MOD_Z + MOD_H, ('Nguồn rộng', 'Nguồn dài', 'Nguồn cao')))
CELL_TOP = CELL_Z + CELL_D / 2
model.measure('cell', 'Pin', kind='component', follow='cell', visible_with='cell', lines=[
    dim((CELL_X - CELL_D / 2, -CELL_L / 2, CELL_TOP), (CELL_X + CELL_D / 2, -CELL_L / 2, CELL_TOP),
        (0, -5, 0), 'Pin', (0, -5, 2), prefix='Ø'),
    dim((CELL_X + CELL_D / 2, -CELL_L / 2, CELL_TOP), (CELL_X + CELL_D / 2, CELL_L / 2, CELL_TOP),
        (5, 0, 0), 'Pin dài', (13, 0, 3)),
])

LID_OPEN, CAP_OPEN = (0, 0, 65), (0, -24, 0)
model.animation('explode', 'Mở hộp', duration=10,
                open_pose={'batteryLid': LID_OPEN, 'electronicsLid': LID_OPEN, 'board': (0, 0, 24),
                           'converter': (0, 0, 20), 'cell': (0, 0, 27), 'usbCap': CAP_OPEN},
                tracks={'batteryLid': pulse(LID_OPEN), 'electronicsLid': pulse(LID_OPEN),
                        'board': pulse((0, 0, 24)), 'converter': pulse((0, 0, 20)),
                        'cell': pulse((0, 0, 27)), 'usbCap': pulse(CAP_OPEN)},
                camera=pulse((0, 0, 25)), measure_reveal=(0.34, 0.64))
model.animation('battery', 'Thay pin', duration=10,
                open_pose={'batteryLid': LID_OPEN, 'cell': (0, 0, 40)},
                tracks={'batteryLid': [(0, (0, 0, 0)), (0.08, (0, 0, 0)), (0.256, LID_OPEN),
                                       (0.8325, LID_OPEN), (0.97, (0, 0, 0)), (1, (0, 0, 0))],
                        'cell': [(0, (0, 0, 0)), (0.224, (0, 0, 0)), (0.4, (0, 0, 40)),
                                 (0.72, (0, 0, 40)), (0.8575, (0, 0, 0)), (1, (0, 0, 0))]},
                camera=pulse((0, 0, 25)), measure_reveal=(0.34, 0.64))
model.animation('usb', 'Bịt USB', duration=10, open_pose={'usbCap': CAP_OPEN},
                tracks={'usbCap': pulse(CAP_OPEN)}, camera=pulse((0, 0, 0)), measure_reveal=(0.34, 0.64))


def lids():
    return {'batteryLid': battery_lid(), 'electronicsLid': electronics_lid()}


@model.check('Lids without friction ribs clear base')
def lids_clear_base():
    for name in LIDS:
        clear(installed_lid(name, False), base=base())


@model.check('Independent lids clear')
def lids_clear_each_other():
    clear(battery_lid(), electronicsLid=electronics_lid())


@model.check('Reference envelopes clear')
def references_clear():
    # The whole rectangular converter and holder envelopes, not just the drawn components.
    envelopes = [(piece.name, box_solid(piece)) for piece in BOARD + CONVERTER]
    envelopes += [('holder', HOLDER), ('cell', CELL),
                  ('module_envelope', block(MOD_W, MOD_L, MOD_H, MOD_X, MOD_Y, MOD_Z)),
                  ('holder_envelope', block(HOLDER_W, HOLDER_L, HOLDER_H, CELL_X, z=HOLDER_Z))]
    for name, envelope in envelopes:
        try:
            clear(envelope, base=base(), usbCap=usb_cap(), **lids())
        except CheckFailed as error:
            raise CheckFailed(f'{name} {error}') from None


@model.check('USB cap without ribs clears base')
def usb_cap_clears_base():
    clear(installed_usb_cap(False), base=base())


@model.check('USB cap clears lids')
def usb_cap_clears_lids():
    clear(usb_cap(), **lids())


@model.check('Continuous USB cap withdrawal clear')
def usb_cap_withdrawal():
    # Swept prisms cover every point of the cap during straight withdrawal; ribs omitted.
    travel = 24
    face = block(USB_W + 3, USB_CAP_FACE_T + travel, BASE_H - USB_BOTTOM + 3,
                 ESP_X, -L / 2 - (USB_CAP_FACE_T + travel) / 2, USB_BOTTOM - 1.5)
    tongue = block(USB_W - 2 * FIT, USB_CAP_DEPTH + EPS + travel, BASE_H - USB_BOTTOM - 2 * FIT,
                   ESP_X, -L / 2 + (USB_CAP_DEPTH - EPS - travel) / 2, USB_BOTTOM + FIT)
    clear(face.union(tongue), base=base(), **lids())


@model.check('Continuous battery removal clear')
def battery_removal():
    sweep = CELL.union(CELL.translate((0, 0, 45))).union(block(CELL_D, CELL_L, 45, CELL_X, z=CELL_Z))
    clear(sweep, base=base(), holder=HOLDER, electronicsLid=electronics_lid())


@model.check('USB cable 12x6 clear')
def usb_cable():
    # Checked with the removable cap taken out.
    clear(block(12, 12, 6, ESP_X, -44, ESP_Z + 1.6 - 1.4), base=base(), **lids())


@model.check('USB cap clears board socket')
def usb_socket_gap():
    usb = next(piece for piece in BOARD if piece.name == 'usb')
    gap = usb.center[1] - usb.size[1] / 2 - usb_cap().val().BoundingBox().ymax
    if gap <= 1:
        raise CheckFailed(f'gap {gap:.3f} mm is not above 1 mm')
    return {'socket_clearance_mm': round(gap, 3)}
