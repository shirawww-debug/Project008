import numpy as np

from bfid import features as F


def test_summary_features_shape():
    rng = np.random.default_rng(0)
    windows = rng.normal(size=(10, 32, 7))
    feats = F.summary_features(windows)
    assert feats.shape == (10, 4 * 7)


def test_normalize_windows_zero_mean():
    rng = np.random.default_rng(1)
    windows = rng.normal(loc=5.0, scale=2.0, size=(4, 50, 3))
    norm = F.normalize_windows(windows)
    assert np.allclose(norm.mean(axis=1), 0, atol=1e-6)


def test_summary_features_rejects_bad_shape():
    try:
        F.summary_features(np.zeros((10, 5)))
    except ValueError:
        return
    raise AssertionError("forme invalide non détectée")
