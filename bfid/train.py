"""Orchestration : données -> fenêtres -> évaluation du classifieur."""

from __future__ import annotations

import numpy as np

from . import baseline, synthetic
from .baseline import EvalResult
from .dataset import BfiSample, build_windows, windowize


def _windows_with_groups(
    samples: list[BfiSample], window: int, stride: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construit X, y, et un id de groupe (= une trace) par fenêtre."""
    xs, ys, gs = [], [], []
    for gid, s in enumerate(samples):
        w = windowize(s.frame_matrix(), window, stride)
        if w.shape[0] == 0:
            continue
        xs.append(w)
        ys.append(np.full(w.shape[0], s.label, dtype=int))
        gs.append(np.full(w.shape[0], gid, dtype=int))
    if not xs:
        raise ValueError("Aucune fenêtre produite")
    return (np.concatenate(xs), np.concatenate(ys), np.concatenate(gs))


def evaluate_samples(
    samples: list[BfiSample],
    window: int = 32,
    stride: int = 8,
    seed: int = 0,
) -> EvalResult:
    """Évalue le baseline sur une liste de samples (validation croisée groupée)."""
    x, y, groups = _windows_with_groups(samples, window, stride)
    return baseline.cross_validate(x, y, groups, seed=seed)


def run_demo(
    n_persons: int = 5,
    traces_per_person: int = 8,
    n_frames: int = 200,
    window: int = 32,
    stride: int = 8,
    seed: int = 0,
    label_prefix: str = "person",
) -> EvalResult:
    """Génère un dataset synthétique et évalue le baseline de bout en bout."""
    samples = synthetic.generate_dataset(
        n_persons=n_persons,
        traces_per_person=traces_per_person,
        n_frames=n_frames,
        seed=seed,
        label_prefix=label_prefix,
    )
    return evaluate_samples(samples, window=window, stride=stride, seed=seed)
