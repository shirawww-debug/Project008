import math

import numpy as np
import pytest

from bfid import angles as A


def test_layout_4x4_matches_standard():
    layout = A.angle_layout(4, 4)
    expected = [
        ("phi", 1, 1), ("phi", 2, 1), ("phi", 3, 1),
        ("psi", 2, 1), ("psi", 3, 1), ("psi", 4, 1),
        ("phi", 2, 2), ("phi", 3, 2),
        ("psi", 3, 2), ("psi", 4, 2),
        ("phi", 3, 3),
        ("psi", 4, 3),
    ]
    assert layout == expected


@pytest.mark.parametrize("nr,nc,n_phi,n_psi", [
    (2, 1, 1, 1),
    (3, 2, 3, 3),
    (4, 2, 5, 5),
    (4, 3, 6, 6),
    (4, 4, 6, 6),
])
def test_num_angles(nr, nc, n_phi, n_psi):
    assert A.num_angles(nr, nc) == (n_phi, n_psi)


@pytest.mark.parametrize("b", [2, 4, 6, 7, 9])
def test_phi_roundtrip_and_range(b):
    rng = np.random.default_rng(b)
    for _ in range(200):
        angle = rng.uniform(0, 2 * math.pi)
        k = A.quantize_phi(angle, b)
        assert 0 <= k < 2 ** b
        dq = A.dequantize_phi(k, b)
        assert 0 <= dq < 2 * math.pi
        assert abs(dq - angle) <= A.phi_step(b)


@pytest.mark.parametrize("b", [2, 4, 5, 7])
def test_psi_roundtrip_and_range(b):
    rng = np.random.default_rng(b + 100)
    for _ in range(200):
        angle = rng.uniform(0, math.pi / 2)
        k = A.quantize_psi(angle, b)
        assert 0 <= k < 2 ** b
        dq = A.dequantize_psi(k, b)
        assert 0 <= dq < math.pi / 2
        assert abs(dq - angle) <= A.psi_step(b)


def test_invalid_dimensions():
    with pytest.raises(ValueError):
        A.angle_layout(1, 1)
    with pytest.raises(ValueError):
        A.angle_layout(2, 3)
