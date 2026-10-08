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
