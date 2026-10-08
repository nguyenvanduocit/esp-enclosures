import itertools
import math
import random

import numpy as np

from printkit.pose import euler_xyz_matrix, installed_pose, matrix_euler_xyz


def test_y_half_turn_matrix():
    assert np.allclose(euler_xyz_matrix((0, 180, 0)), np.diag([-1, 1, -1]))


def test_matches_three_js_order():
    # three.js Euler 'XYZ' builds Rx @ Ry @ Rz.
    x, y, z = 30, 20, 10
    rx = euler_xyz_matrix((x, 0, 0))
    ry = euler_xyz_matrix((0, y, 0))
    rz = euler_xyz_matrix((0, 0, z))
    assert np.allclose(euler_xyz_matrix((x, y, z)), rx @ ry @ rz)


def test_matrix_round_trip():
    rng = random.Random(1)
    for _ in range(200):
        angles = (rng.uniform(-179, 179), rng.uniform(-89, 89), rng.uniform(-179, 179))
        assert np.allclose(
            matrix_euler_xyz(euler_xyz_matrix(angles)), angles, atol=1e-9
        )


def test_single_axis_inverse_is_readable():
    assert installed_pose((0, 180, 0), (0, 0, 0))[1] == [0.0, 180.0, 0.0]
    assert installed_pose((90, 0, 0), (0, 0, 0))[1] == [-90.0, 0.0, 0.0]
    assert installed_pose((0, 0, 0), (0, 0, 0)) == ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])


def test_installed_pose_inverts_any_rotation():
    rng = random.Random(2)
    rotations = [
        (rng.uniform(-180, 180), rng.uniform(-89, 89), rng.uniform(-180, 180))
        for _ in range(20)
    ]
    rotations += list(itertools.product((0, 90, 180, -90), repeat=3))
    for rotation in rotations:
        translation = np.array([rng.uniform(-50, 50) for _ in range(3)])
        point = np.array([rng.uniform(-20, 20) for _ in range(3)])
        printed = euler_xyz_matrix(rotation) @ point + translation
        position, viewer_rotation = installed_pose(rotation, translation)
        restored = euler_xyz_matrix(viewer_rotation) @ printed + np.array(position)
        assert np.allclose(restored, point, atol=1e-4), rotation
