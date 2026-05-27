"""Extraction de features à partir de fenêtres temporelles d'angles BFI.

Deux représentations :

  * `summary_features` : statistiques par fenêtre (moyenne, écart-type, deltas)
    -> vecteur compact pour les classifieurs classiques (RandomForest/SVM).
  * les fenêtres brutes (N, window, D) alimentent directement le CNN
    temporel (voir model.py).

Note : la phase des angles est traitée comme un réel. Pour une fidélité accrue
on pourrait encoder phi via (sin, cos) afin de gérer la circularité ; gardé
simple ici car les angles synthétiques ne wrappent pas. Voir docs/ROADMAP.md.
"""

from __future__ import annotations

import numpy as np


def summary_features(windows: np.ndarray) -> np.ndarray:
    """(N, window, D) -> (N, 4*D) : moyenne, std, et moyenne/std des deltas."""
    if windows.ndim != 3:
        raise ValueError("windows doit être de forme (N, window, D)")
    mean = windows.mean(axis=1)
    std = windows.std(axis=1)
    deltas = np.diff(windows, axis=1)
    dmean = deltas.mean(axis=1)
    dstd = deltas.std(axis=1)
    return np.concatenate([mean, std, dmean, dstd], axis=1)


def normalize_windows(windows: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Normalise chaque fenêtre par canal (z-score sur l'axe temps)."""
    mean = windows.mean(axis=1, keepdims=True)
    std = windows.std(axis=1, keepdims=True)
    return (windows - mean) / (std + eps)
