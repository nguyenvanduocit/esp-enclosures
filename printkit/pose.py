"""Rotation maths shared by export and tests; matches three.js Euler order 'XYZ'."""

import math

import numpy as np


def euler_xyz_matrix(degrees):
    x, y, z = (math.radians(value) for value in degrees)
    rx = np.array(
        [[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]]
    )
    ry = np.array(
        [[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]]
    )
    rz = np.array(
        [[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]]
    )
    return rx @ ry @ rz


def matrix_euler_xyz(matrix):
    m = np.asarray(matrix, dtype=float)
    y = math.asin(max(-1.0, min(1.0, m[0, 2])))
    if abs(m[0, 2]) < 0.9999999:
        x, z = math.atan2(-m[1, 2], m[2, 2]), math.atan2(-m[0, 1], m[0, 0])
    else:
        x, z = math.atan2(m[2, 1], m[1, 1]), 0.0
    return tuple(math.degrees(value) for value in (x, y, z))


def tidy(values, digits=6):
    return [round(float(value), digits) + 0.0 for value in values]


def half_open(angle):
    """Angle in (-180, 180]."""
    angle = (angle + 180) % 360 - 180
    return 180.0 if angle == -180 else angle


def installed_pose(print_rotation, translation):
    """Viewer pose mapping a print-frame mesh back to its installed pose.

    The print frame is `euler_xyz_matrix(print_rotation) @ installed + translation`.
    """
    inverse = euler_xyz_matrix(print_rotation).T
    position = -inverse @ np.asarray(translation, dtype=float)
    if sum(1 for angle in print_rotation if angle) <= 1:
        # A single-axis rotation inverts to its negation, which keeps poses readable.
        rotation = [half_open(-angle) for angle in print_rotation]
    else:
        rotation = matrix_euler_xyz(inverse)
    return tidy(position), tidy(rotation)
