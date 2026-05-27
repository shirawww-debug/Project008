"""Classifieur baseline (scikit-learn) sur features statistiques.

Tourne sans matériel ni GPU. Sert de référence avant d'investir dans le CNN
temporel (model.py). L'évaluation se fait par validation croisée groupée :
les fenêtres d'une même trace ne doivent jamais se retrouver à la fois dans le
train et le test (sinon fuite de données et accuracy trompeuse).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import features as F


def make_classifier(n_estimators: int = 200, seed: int = 0) -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=n_estimators, random_state=seed, n_jobs=-1)),
    ])


@dataclass
class EvalResult:
    accuracy: float
    per_fold: list[float]
    confusion: np.ndarray
    n_classes: int

    def __str__(self) -> str:
        folds = ", ".join(f"{a:.3f}" for a in self.per_fold)
        return (
            f"accuracy={self.accuracy:.4f} (chance={1/self.n_classes:.3f}) "
            f"| folds=[{folds}]"
        )


def cross_validate(
    windows: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
    seed: int = 0,
) -> EvalResult:
    """Validation croisée groupée. `groups` = id de trace par fenêtre."""
    x = F.summary_features(windows)
    n_classes = len(np.unique(y))
    n_splits = min(n_splits, np.bincount(y).min(), len(np.unique(groups)))
    n_splits = max(2, n_splits)
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    accs, cms = [], []
    for train_idx, test_idx in skf.split(x, y, groups):
        clf = make_classifier(seed=seed)
        clf.fit(x[train_idx], y[train_idx])
        pred = clf.predict(x[test_idx])
        accs.append(accuracy_score(y[test_idx], pred))
        cms.append(confusion_matrix(y[test_idx], pred, labels=range(n_classes)))
    return EvalResult(
        accuracy=float(np.mean(accs)),
        per_fold=[float(a) for a in accs],
        confusion=np.sum(cms, axis=0),
        n_classes=n_classes,
    )
