"""Geometric design checks; a failed check raises CheckFailed with the obstacle name."""


class CheckFailed(AssertionError):
    pass


def overlap(a, b):
    return a.intersect(b).val().Volume()


def clear(subject, **obstacles):
    for name, obstacle in obstacles.items():
        volume = overlap(subject, obstacle)
        if volume >= 1e-6:
            raise CheckFailed(f'overlaps {name} by {volume:.4f} mm³')
