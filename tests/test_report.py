import math

import numpy as np
import pytest

from bfid import angles as A
from bfid.mimo_control import VhtMimoControl
from bfid.report import (
    CompressedBeamformingReport,
    build_action_body,
    parse_action_body,
)

CONFIGS = [
    VhtMimoControl(nc=1, nr=2, channel_width=0, grouping=2, codebook=1, feedback_type=0),
    VhtMimoControl(nc=2, nr=3, channel_width=1, grouping=2, codebook=0, feedback_type=0),
    VhtMimoControl(nc=2, nr=4, channel_width=0, grouping=2, codebook=1, feedback_type=1),
]


@pytest.mark.parametrize("mimo", CONFIGS)
def test_action_body_roundtrip(mimo):
    rng = np.random.default_rng(abs(hash(str(mimo))) % 2**32)
    ns = mimo.num_subcarriers
    n_phi, n_psi = A.num_angles(mimo.nr, mimo.nc)
    b_psi, b_phi = mimo.bits_psi_phi

    phi = rng.uniform(0, 2 * math.pi, size=(ns, n_phi))
    psi = rng.uniform(0, math.pi / 2, size=(ns, n_psi))
    snr = rng.integers(-128, 128, size=mimo.nc).astype(np.int8)

    rep = CompressedBeamformingReport(mimo, snr, phi, psi)
    decoded = parse_action_body(build_action_body(rep))

    assert decoded.phi.shape == (ns, n_phi)
    assert decoded.psi.shape == (ns, n_psi)
    np.testing.assert_array_equal(decoded.avg_snr_raw, snr)
    # Les angles décodés sont à au plus un pas de quantification de l'original.
    assert np.all(np.abs(decoded.phi - phi) <= A.phi_step(b_phi) + 1e-9)
    assert np.all(np.abs(decoded.psi - psi) <= A.psi_step(b_psi) + 1e-9)


def test_idempotent_after_first_decode():
    mimo = CONFIGS[0]
    rng = np.random.default_rng(7)
    ns = mimo.num_subcarriers
    n_phi, n_psi = A.num_angles(mimo.nr, mimo.nc)
    rep = CompressedBeamformingReport(
        mimo,
        np.zeros(mimo.nc, dtype=np.int8),
        rng.uniform(0, 2 * math.pi, size=(ns, n_phi)),
        rng.uniform(0, math.pi / 2, size=(ns, n_psi)),
    )
    once = parse_action_body(build_action_body(rep))
    twice = parse_action_body(build_action_body(once))
    np.testing.assert_allclose(once.phi, twice.phi)
    np.testing.assert_allclose(once.psi, twice.psi)


def test_rejects_non_vht_frame():
    with pytest.raises(ValueError):
        parse_action_body(bytes([1, 0, 0, 0, 0, 0]))
