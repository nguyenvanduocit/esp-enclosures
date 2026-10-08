"""Geometric design checks; a failed check raises CheckFailed with the obstacle name."""
import manifold3d as m3

from printkit.art import to_manifold


class CheckFailed(AssertionError):
    pass


def overlap(a, b):
    """Intersection volume in mm³ of two CadQuery solids or Manifolds, in any mix.

    With a Manifold on either side both are meshed and intersected as Manifolds; CadQuery
    solids are tessellated at 0.02 mm, so expect float noise near 1e-6 mm³ at touching faces."""
    if isinstance(a, m3.Manifold) or isinstance(b, m3.Manifold):
        a, b = (shape if isinstance(shape, m3.Manifold) else to_manifold(shape) for shape in (a, b))
        return (a ^ b).volume()
    return a.intersect(b).val().Volume()


def clear(subject, **obstacles):
    for name, obstacle in obstacles.items():
        volume = overlap(subject, obstacle)
        if volume >= 1e-6:
            raise CheckFailed(f'overlaps {name} by {volume:.4f} mm³')
