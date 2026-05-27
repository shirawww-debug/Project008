"""Conteneurs de données et découpage en fenêtres temporelles.

Un `BfiSample` représente une trace continue de trames BFI pour une personne
(par ex. un trajet dans la pièce) : séquences d'angles phi/psi indexées par
le temps. Le pipeline ML travaille sur des fenêtres glissantes de ces traces.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BfiSample:
    phi: np.ndarray            # (T, ns, n_phi)
    psi: np.ndarray            # (T, ns, n_psi)
    label: int                 # identifiant de la personne (entier)
    person: str = ""           # nom/étiquette lisible
    meta: dict = field(default_factory=dict)

    @property
    def n_frames(self) -> int:
        return self.phi.shape[0]

    def frame_matrix(self) -> np.ndarray:
        """Aplati chaque trame en un vecteur (T, ns*(n_phi+n_psi))."""
        t = self.phi.shape[0]
        return np.concatenate(
            [self.phi.reshape(t, -1), self.psi.reshape(t, -1)], axis=1
        )


def windowize(
    frames: np.ndarray, window: int, stride: int
) -> np.ndarray:
    """Découpe (T, D) en fenêtres (n_windows, window, D)."""
    t = frames.shape[0]
    if t < window:
        return np.empty((0, window, frames.shape[1]), dtype=frames.dtype)
    starts = range(0, t - window + 1, stride)
    return np.stack([frames[s:s + window] for s in starts], axis=0)


def build_windows(
    samples: list[BfiSample], window: int = 32, stride: int = 8
) -> tuple[np.ndarray, np.ndarray]:
    """Transforme une liste de samples en (X, y).

    X : (N, window, D) séquences de trames aplaties.
    y : (N,) labels.
    """
    xs, ys = [], []
    for s in samples:
        w = windowize(s.frame_matrix(), window, stride)
        if w.shape[0] == 0:
            continue
        xs.append(w)
        ys.append(np.full(w.shape[0], s.label, dtype=int))
    if not xs:
        raise ValueError("Aucune fenêtre produite (traces trop courtes ?)")
    return np.concatenate(xs, axis=0), np.concatenate(ys, axis=0)


def save_samples(path: str, samples: list[BfiSample]) -> None:
    """Sérialise une liste de samples dans un .npz."""
    arrays = {}
    labels, persons = [], []
    for i, s in enumerate(samples):
        arrays[f"phi_{i}"] = s.phi
        arrays[f"psi_{i}"] = s.psi
        labels.append(s.label)
        persons.append(s.person)
    arrays["labels"] = np.asarray(labels, dtype=int)
    arrays["persons"] = np.asarray(persons, dtype=object)
    arrays["count"] = np.asarray(len(samples))
    np.savez_compressed(path, **arrays)


def load_samples(path: str) -> list[BfiSample]:
    data = np.load(path, allow_pickle=True)
    n = int(data["count"])
    out = []
    for i in range(n):
        out.append(
            BfiSample(
                phi=data[f"phi_{i}"],
                psi=data[f"psi_{i}"],
                label=int(data["labels"][i]),
                person=str(data["persons"][i]),
            )
        )
    return out
