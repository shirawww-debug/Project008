import numpy as np

from bfid import synthetic, train
from bfid.dataset import build_windows, load_samples, save_samples


def test_synthetic_shapes():
    samples = synthetic.generate_dataset(
        n_persons=3, traces_per_person=2, n_frames=50, roundtrip=False)
    assert len(samples) == 6
    s = samples[0]
    n_phi, n_psi = 1, 1  # config 2x1 par défaut
    assert s.phi.shape == (50, 16, n_phi)
    assert s.psi.shape == (50, 16, n_psi)
    assert {sm.label for sm in samples} == {0, 1, 2}


def test_signature_is_deterministic():
    a = synthetic.generate_sample(label=1, person="p", n_frames=20, seed=3)
    b = synthetic.generate_sample(label=1, person="p", n_frames=20, seed=3)
    np.testing.assert_allclose(a.phi, b.phi)


def test_windows_shape():
    samples = synthetic.generate_dataset(
        n_persons=2, traces_per_person=1, n_frames=100, roundtrip=False)
    x, y = build_windows(samples, window=32, stride=8)
    assert x.ndim == 3 and x.shape[1] == 32
    assert x.shape[0] == y.shape[0]


def test_save_load_roundtrip(tmp_path):
    samples = synthetic.generate_dataset(
        n_persons=2, traces_per_person=1, n_frames=30, roundtrip=False)
    path = str(tmp_path / "ds.npz")
    save_samples(path, samples)
    loaded = load_samples(path)
    assert len(loaded) == len(samples)
    np.testing.assert_allclose(loaded[0].phi, samples[0].phi)
    assert loaded[0].label == samples[0].label


def test_baseline_beats_chance():
    # Le générateur synthétique doit produire des personnes séparables :
    # l'accuracy doit dépasser nettement le hasard (1/5 = 0.2).
    result = train.run_demo(
        n_persons=5, traces_per_person=8, n_frames=160,
        window=32, stride=8, seed=0)
    assert result.n_classes == 5
    assert result.accuracy > 0.6, result
