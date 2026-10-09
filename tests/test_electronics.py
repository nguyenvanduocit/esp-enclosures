from pytest import approx

from printkit.library.electronics import esp32_c3_supermini


def test_supermini_envelope():
    pieces = esp32_c3_supermini(at=(14, -26.5, 12))
    assert [piece.name for piece in pieces][:5] == ['pcb', 'usb', 'chip', 'antenna', 'header_-1']
    assert len(pieces) == 22
    by_name = {piece.name: piece for piece in pieces}
    assert by_name['pcb'].center == approx((14, -26.5, 12.8))
    assert by_name['usb'].center == approx((14, -35.65, 15.2))
    assert by_name['pin_1_7'].center == approx((21.62, -17.61, 9.25))


import cadquery as cq

from printkit.library.electronics import bme280, hc_sr501, ili9341_24, mpu6050, tp4056_usbc


def top(pieces):
    return max(p.center[2] + p.size[2] / 2 for p in pieces if hasattr(p, 'size'))


def test_tp4056_usbc_envelope():
    pieces = tp4056_usbc(at=(36, 17.5, 16.75))
    by_name = {p.name: p for p in pieces}
    assert by_name['pcb'].size == (17, 28, 1.6)
    assert top(pieces) - 16.75 == approx(4.9)                      # listings: 4.1 to 4.9 mm tall
    assert by_name['usb'].center[2] == approx(16.75 + 1.6 + 1.65)  # USB-C axis 3.25 above the PCB underside
    assert by_name['usb'].center[1] - 3.75 == approx(17.5 - 14 - 0.8)  # port overhangs the -y edge by 0.8


def test_bme280_envelope():
    by_name = {p.name: p for p in bme280(at=(10, 9, 8.75))}
    assert by_name['pcb'].size == (15.4, 11.6, 1.6)
    assert by_name['header'].center[2] == approx(8.75 - 1.25)


def test_mpu6050_envelope():
    by_name = {p.name: p for p in mpu6050(at=(20, 20, 6))}
    assert by_name['pcb'].size == (20.5, 16, 1.6)
    assert by_name['header'].size == (20.32, 2.5, 2.5)


def test_hc_sr501_lens_is_a_solid_above_the_pcb():
    pieces = hc_sr501(at=(20, 20, 19.8))
    lens = next(p for p in pieces if p.name == 'lens')
    box = lens.shape.val().BoundingBox()
    assert (box.zmin, box.zmax) == approx((19.8 + 1.2, 19.8 + 1.2 + 18))
    assert box.xlen == approx(23)


def test_ili9341_envelope():
    by_name = {p.name: p for p in ili9341_24(at=(40, 25.55, 12.9))}
    assert by_name['pcb'].size == (70.5, 43.3, 1.6)
    assert by_name['glass'].center[2] + 1.6 == approx(12.9 + 1.6 + 3.2)  # glass top
