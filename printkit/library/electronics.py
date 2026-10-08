"""Reference envelopes for common electronics. Component positions are illustrative, not measured."""
from printkit.manifest import Box

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
