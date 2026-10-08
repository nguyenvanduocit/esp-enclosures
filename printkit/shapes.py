"""CadQuery building blocks. Boxes sit on their Z origin and are centred in X/Y."""
import cadquery as cq
import manifold3d as m3
import numpy as np

from printkit.pose import euler_xyz_matrix


def block(w, length, height, x=0, y=0, z=0):
    return cq.Workplane('XY').box(w, length, height, centered=(True, True, False)).translate((x, y, z))


def rounded(w, length, height, radius, x=0, y=0, z=0):
    return block(w, length, height, x, y, z).edges('|Z').fillet(radius)


def box_solid(box):
    w, length, height = box.size
    x, y, z = box.center
    return block(w, length, height, x, y, z - height / 2)


def rotated(shape, degrees):
    """Rotate about world axes so the result equals pose.euler_xyz_matrix(degrees)."""
    x, y, z = degrees
    for axis, angle in (((0, 0, 1), z), ((0, 1, 0), y), ((1, 0, 0), x)):
        if angle:
            shape = shape.rotate((0, 0, 0), axis, angle)
    return shape


def placed(shape, degrees, position):
    """Rotate a CadQuery shape or a Manifold by Euler XYZ `degrees` about the origin, then translate."""
    if isinstance(shape, m3.Manifold):
        return shape.transform(np.hstack([euler_xyz_matrix(degrees), np.reshape(position, (3, 1))]))
    return rotated(shape, degrees).translate(tuple(position))
