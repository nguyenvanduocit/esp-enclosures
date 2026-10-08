"""ESP32-C3 SuperMini enclosure; millimetres, USB on the negative Y side."""
from functools import cache

import cadquery as cq

from printkit import Drag, Model, dim, pulse
from printkit.checks import CheckFailed, clear
from printkit.library.electronics import SUPERMINI_PCB, esp32_c3_supermini
from printkit.shapes import block, box_solid, rounded

PCB_W, PCB_L, PCB_T = SUPERMINI_PCB
OUTER_W, OUTER_L = 26.4, 32.0
WALL, FLOOR, LID_T = 1.8, 1.8, 1.8
HEADER_SPACE = 10.0
PCB_Z = FLOOR + HEADER_SPACE
BASE_H = PCB_Z + PCB_T + 5.0
HEIGHT = BASE_H + LID_T
INNER_W, INNER_L = OUTER_W - 2 * WALL, OUTER_L - 2 * WALL
CORNER_R = 3.0
FIT = 0.20
SKIRT_H, SKIRT_WALL = 2.4, 1.2
USB_W, USB_BOTTOM = 14.0, PCB_Z - 0.8
EPS = 0.02
BOARD = esp32_c3_supermini(at=(0, 0, PCB_Z))

model = Model(
    'esp32-c3-supermini', title='ESP32-C3 SuperMini',
    description='Hộp gọn cho bo đã hàn chân, cấp nguồn qua USB-C.',
    category='Hộp điện tử', status='Chưa in thử', thumbnail='thumbnail.png',
    dimensions=(OUTER_W, OUTER_L, HEIGHT),
    camera={'position': [63, -88, 69], 'target': [0, 0, 12], 'minDistance': 28, 'maxDistance': 230,
            'views': [{'id': 'front', 'label': 'Trước', 'offset': [0, -115, 0.01]},
                      {'id': 'top', 'label': 'Trên', 'offset': [0, -0.01, 115]}]},
    grid={'size': 100, 'divisions': 20},
    print_info={'summary': 'Chưa in thử', 'sections': [
        {'title': 'Độ vừa', 'rows': [],
         'notes': ['Bo và linh kiện là mô hình tham khảo. Đo bo thực và in thử để kiểm tra độ vừa.'],
         'links': []}]})


@model.part('base', 'Thân', color='#367c85', drag=Drag((0, 0, -1), 35))
def base():
    shell = rounded(OUTER_W, OUTER_L, BASE_H, CORNER_R)
    cavity = rounded(INNER_W, INNER_L, BASE_H, CORNER_R - WALL, z=FLOOR)
    shell = shell.cut(cavity)
    # Supports stay inside the 15.24 mm header spacing, clear of the plastic strips.
    for x in (-4.6, 4.6):
        for y in (-7.4, 7.4):
            post = cq.Workplane('XY').circle(1.5).extrude(HEADER_SPACE + EPS)
            shell = shell.union(post.translate((x, y, FLOOR - EPS)))
    for side in (-1, 1):
        for y in (-6.1, 6.1):
            shell = shell.union(block(2.2, 2.2, PCB_Z + PCB_T, x=side * 10.35, y=y))
    shell = shell.union(block(8, 2.75, PCB_Z + PCB_T, y=12.875))
    for x in (-6.8, 6.8):
        shell = shell.union(block(2.8, 2.75, PCB_Z + PCB_T, x=x, y=-12.875))
    # Cut after the locating stops so they cannot obstruct the cable overmould.
    shell = shell.cut(block(USB_W, 8, BASE_H, y=-OUTER_L / 2, z=USB_BOTTOM))
    return shell.clean()


@cache
def printed_lid(with_ribs=True):
    # Lid modelled exterior-face down; its skirt grows upward.
    lid = rounded(OUTER_W, OUTER_L, LID_T, CORNER_R)
    skirt = rounded(INNER_W - 2 * FIT, INNER_L - 2 * FIT, SKIRT_H + EPS, 1.0, z=LID_T - EPS)
    skirt = skirt.cut(rounded(INNER_W - 2 * (FIT + SKIRT_WALL), INNER_L - 2 * (FIT + SKIRT_WALL),
                              SKIRT_H + 2 * EPS, 0.6, z=LID_T - 2 * EPS))
    # Interrupt the front skirt so the cable opening remains unobstructed.
    skirt = skirt.cut(block(USB_W + 0.6, 7, SKIRT_H + 2 * EPS, y=-INNER_L / 2, z=LID_T - EPS))
    lid = lid.union(skirt)
    if with_ribs:
        for side in (-1, 1):
            for y in (-6.5, 6.5):
                rib = cq.Workplane('XY').circle(0.35).extrude(SKIRT_H + EPS)
                # 0.08 mm local interference; fit must be calibrated on a print.
                lid = lid.union(rib.translate((side * (INNER_W / 2 - 0.27), y, LID_T - EPS)))
    for y in (-3.2, 0, 3.2):
        vent = cq.Workplane('XY').slot2D(12, 1.4).extrude(LID_T + 2 * EPS)
        lid = lid.cut(vent.translate((0, y, -EPS)))
    return lid.clean()


def installed(lid_shape):
    return lid_shape.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, HEIGHT))


@model.part('lid', 'Nắp', color='#ded4ba', drag=Drag((0, 0, 1), 65), print_rotation=(0, 180, 0))
def lid():
    return installed(printed_lid())


model.reference('board', 'ESP32', BOARD, drag=Drag((0, 0, 1), 50))


model.measure('case', 'Vỏ hộp', kind='case', follow='base', label_width=20, lines=[
    dim((-OUTER_W / 2, -OUTER_L / 2, 0), (OUTER_W / 2, -OUTER_L / 2, 0), (0, -4, 0), 'Rộng', (0, -2.4, 0)),
    dim((OUTER_W / 2, -OUTER_L / 2, 0), (OUTER_W / 2, OUTER_L / 2, 0), (4, 0, 0), 'Dài', (4.8, 0, 0)),
    dim((-OUTER_W / 2, -OUTER_L / 2, 0), (-OUTER_W / 2, -OUTER_L / 2, HEIGHT), (-4, 0, 0), 'Cao vỏ', (-5.6, 0, 0)),
])
PCB_TOP = PCB_Z + PCB_T
model.measure('board', 'PCB ESP32', kind='component', follow='board', visible_with='board', label_width=20, lines=[
    dim((-PCB_W / 2, -PCB_L / 2, PCB_TOP), (PCB_W / 2, -PCB_L / 2, PCB_TOP), (0, -5, 0), 'PCB rộng', (0, -5, 2)),
    dim((PCB_W / 2, -PCB_L / 2, PCB_TOP), (PCB_W / 2, PCB_L / 2, PCB_TOP), (5, 0, 0), 'PCB dài', (8, 0, 3)),
    dim((-PCB_W / 2, PCB_L / 2, PCB_Z), (-PCB_W / 2, PCB_L / 2, PCB_TOP), (-5, 0, 0), 'PCB dày', (-8, 0, 3)),
])
model.animation('explode', 'Mở hộp', duration=10, open_pose={'lid': (0, 0, 32), 'board': (0, 0, 15)},
                tracks={'lid': pulse((0, 0, 32)), 'board': pulse((0, 0, 15))},
                camera=pulse((0, 0, 14)), measure_reveal=(0.34, 0.64))


@model.check('Lid without friction ribs clears base')
def lid_clears_base():
    clear(installed(printed_lid(False)), base=base())


@model.check('Reference board and headers clear')
def board_clear():
    for piece in BOARD:
        try:
            clear(box_solid(piece), base=base(), lid=lid())
        except CheckFailed as error:
            raise CheckFailed(f'{piece.name} {error}') from None


@model.check('Cable envelope 12x6 clear')
def cable_clear():
    clear(block(12, 10, 6, y=-17.5, z=PCB_Z + PCB_T - 1.4), base=base(), lid=lid())
