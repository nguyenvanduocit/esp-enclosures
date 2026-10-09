"""Reference envelopes for common electronics. Component positions are illustrative, not measured."""
import cadquery as cq

from printkit.manifest import Box, Solid

SUPERMINI_PCB = (18.0, 22.5, 1.6)


def esp32_c3_supermini(at=(0, 0, 0)):
    """ESP32-C3 SuperMini with two downward headers; `at` is the centre of the PCB underside."""
    x, y, z = at
    w, length, t = SUPERMINI_PCB
    top = z + t
    pieces = [Box('pcb', (w, length, t), (x, y, z + t / 2), '#214f55'),
              Box('usb', (9, 7.2, 3.2), (x, y - 9.15, top + 1.6), '#c3cbd0'),
              Box('chip', (5, 5, 1), (x, y, top + 0.5), '#24343c'),
              Box('antenna', (2.5, 3.4, 1.2), (x + 4.3, y + 7.9, top + 0.6), '#d2bda0')]
    for side in (-1, 1):
        pieces.append(Box(f'header_{side}', (2.54, 20.32, 2.5), (x + side * 7.62, y, z - 1.25), '#27343c'))
        for i in range(8):
            pieces.append(Box(f'pin_{side}_{i}', (0.64, 0.64, 11.5),
                              (x + side * 7.62, y + (i - 3.5) * 2.54, z - 2.75), '#c99b49'))
    return pieces


def tp4056_usbc(at=(0, 0, 0)):
    """TP4056 USB-C charger with protection, USB-C towards -y. Listings give 26 to 29 x 17 x 4.1 to 4.9 mm; this is 28 x 17 x 4.9."""
    x, y, z = at
    return [Box('pcb', (17, 28, 1.6), (x, y, z + 0.8), '#2b6fb3'),
            Box('usb', (9, 7.5, 3.3), (x, y - 11.05, z + 1.6 + 1.65), '#c3cbd0'),
            Box('ic', (5, 5, 1.5), (x, y + 4, z + 1.6 + 0.75), '#24343c')]


def bme280(at=(0, 0, 0)):
    """GY-BME280 breakout, 15.4 x 11.6 x 2.4 per listings; the 6-pin header body sits under the board along X."""
    x, y, z = at
    return [Box('pcb', (15.4, 11.6, 1.6), (x, y, z + 0.8), '#6a3fa0'),
            Box('chip', (2.5, 2.5, 0.9), (x + 2, y, z + 1.6 + 0.45), '#c3cbd0'),
            Box('header', (15.24, 2.5, 2.5), (x, y - 3.5, z - 1.25), '#27343c')]


def mpu6050(at=(0, 0, 0)):
    """GY-521 MPU6050, about 20.5 x 16 mm per listings; the 8-pin header body sits under the board along X."""
    x, y, z = at
    return [Box('pcb', (20.5, 16, 1.6), (x, y, z + 0.8), '#2b6fb3'),
            Box('chip', (4, 4, 0.9), (x, y, z + 1.6 + 0.45), '#24343c'),
            Box('header', (20.32, 2.5, 2.5), (x, y - 5, z - 1.25), '#27343c')]


def hc_sr501(at=(0, 0, 0)):
    """HC-SR501 PIR, 32 x 24 mm PCB and a cylindrical lens of diameter 23 and height about 18 (listings disagree, 18 to 30 mm overall)."""
    x, y, z = at
    lens = cq.Workplane('XY').circle(11.5).extrude(18).translate((x, y, z + 1.2))
    return [Box('pcb', (32, 24, 1.2), (x, y, z + 0.6), '#2e8b57'),
            Solid('lens', lens, '#e8e2d0'),
            Box('header', (7.62, 2.5, 2.5), (x + 12, y - 9, z - 1.25), '#27343c')]


def ili9341_24(at=(0, 0, 0)):
    """2.4 inch ILI9341 module, 70.5 x 43.3 mm PCB (Waveshare listing) with the glass above it; the glass size is an assumption."""
    x, y, z = at
    return [Box('pcb', (70.5, 43.3, 1.6), (x, y, z + 0.8), '#2b6fb3'),
            Box('glass', (60, 40, 3.2), (x, y, z + 1.6 + 1.6), '#1c2a33')]
