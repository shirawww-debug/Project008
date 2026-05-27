"""Génération de figures (matplotlib) encodées en PNG base64 pour la webapp."""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")  # backend sans affichage, requis côté serveur
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from ..dataset import BfiSample  # noqa: E402


def _to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")


def confusion_figure(cm: np.ndarray, labels: list[str]) -> str:
    fig, ax = plt.subplots(figsize=(4.5, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.set_xlabel("Prédit")
    ax.set_ylabel("Réel")
    ax.set_title("Matrice de confusion")
    thresh = cm.max() / 2 if cm.max() else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center", fontsize=7,
                    color="white" if cm[i, j] > thresh else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    return _to_base64(fig)


def folds_figure(per_fold: list[float], accuracy: float, chance: float) -> str:
    fig, ax = plt.subplots(figsize=(4.5, 3))
    ax.bar(range(1, len(per_fold) + 1), per_fold, color="#3b7dd8")
    ax.axhline(accuracy, color="#1b4f8a", ls="-", lw=1.5, label=f"moyenne {accuracy:.3f}")
    ax.axhline(chance, color="#c0392b", ls="--", lw=1.5, label=f"hasard {chance:.3f}")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Fold")
    ax.set_ylabel("Accuracy")
    ax.set_title("Accuracy par fold (validation croisée groupée)")
    ax.legend(fontsize=8)
    return _to_base64(fig)


def signature_figure(sample: BfiSample) -> str:
    """Heatmaps temps × sous-porteuse des angles phi et psi (1er angle)."""
    phi = sample.phi[:, :, 0]  # (T, ns)
    psi = sample.psi[:, :, 0]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    for ax, data, name, cmap in (
        (axes[0], phi, "phi (rotation)", "twilight"),
        (axes[1], psi, "psi (élévation)", "viridis"),
    ):
        im = ax.imshow(data.T, aspect="auto", origin="lower", cmap=cmap)
        ax.set_xlabel("Trame (temps)")
        ax.set_ylabel("Sous-porteuse")
        ax.set_title(f"{name} — {sample.person}")
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle(f"Signature BFI ({sample.n_frames} trames)", fontsize=11)
    return _to_base64(fig)


def angle_timeseries_figure(sample: BfiSample, max_carriers: int = 6) -> str:
    """Évolution temporelle de phi pour quelques sous-porteuses."""
    phi = sample.phi[:, :, 0]  # (T, ns)
    ns = phi.shape[1]
    idx = np.linspace(0, ns - 1, min(max_carriers, ns)).astype(int)
    fig, ax = plt.subplots(figsize=(7, 3))
    for c in idx:
        ax.plot(phi[:, c], lw=1, label=f"sc {c}")
    ax.set_xlabel("Trame (temps)")
    ax.set_ylabel("phi (rad)")
    ax.set_title(f"phi dans le temps — {sample.person}")
    ax.legend(fontsize=7, ncol=3)
    return _to_base64(fig)
