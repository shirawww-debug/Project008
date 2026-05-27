"""CNN temporel 1D pour l'identification par BFI (PyTorch, optionnel).

Architecture inspirée des pipelines type BeamSense : convolutions 1D sur l'axe
temporel, les canaux d'entrée étant les angles aplatis (ns*(n_phi+n_psi)).
Alternative légère au Transformer ; suffisant pour quelques dizaines de
personnes.

PyTorch n'est PAS une dépendance du coeur du projet (parsing + baseline
tournent sans). Ce module l'importe paresseusement : `pip install torch` puis
utilisez `train_cnn`. Le baseline sklearn (baseline.py) reste la référence
exécutable par défaut.
"""

from __future__ import annotations

import numpy as np


def _require_torch():
    try:
        import torch  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "PyTorch requis pour le CNN. Installez-le : pip install torch\n"
            "Le baseline sklearn (bfid.baseline) ne nécessite pas torch."
        ) from exc
    import torch
    return torch


def build_cnn(input_channels: int, n_classes: int, seq_len: int):
    """Construit le CNN 1D. Renvoie un nn.Module."""
    torch = _require_torch()
    import torch.nn as nn

    class BfiCNN(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv1d(input_channels, 64, kernel_size=5, padding=2),
                nn.BatchNorm1d(64), nn.ReLU(),
                nn.Conv1d(64, 128, kernel_size=5, padding=2),
                nn.BatchNorm1d(128), nn.ReLU(),
                nn.AdaptiveAvgPool1d(1),
            )
            self.head = nn.Sequential(
                nn.Flatten(), nn.Dropout(0.3), nn.Linear(128, n_classes),
            )

        def forward(self, x):  # x: (B, seq_len, channels)
            x = x.transpose(1, 2)  # -> (B, channels, seq_len)
            return self.head(self.net(x))

    return BfiCNN()


def train_cnn(
    windows: np.ndarray,
    y: np.ndarray,
    n_classes: int,
    epochs: int = 30,
    batch_size: int = 64,
    lr: float = 1e-3,
    val_split: float = 0.2,
    seed: int = 0,
    device: str | None = None,
):
    """Entraîne le CNN. Retourne (modèle, historique). Importe torch à l'appel."""
    torch = _require_torch()
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    torch.manual_seed(seed)
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    x = torch.tensor(windows, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.long)
    n_val = int(len(x) * val_split)
    perm = torch.randperm(len(x), generator=torch.Generator().manual_seed(seed))
    val_idx, train_idx = perm[:n_val], perm[n_val:]

    train_dl = DataLoader(
        TensorDataset(x[train_idx], yt[train_idx]), batch_size=batch_size, shuffle=True)
    val_dl = DataLoader(
        TensorDataset(x[val_idx], yt[val_idx]), batch_size=batch_size)

    model = build_cnn(x.shape[2], n_classes, x.shape[1]).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    history = {"train_loss": [], "val_acc": []}

    for _ in range(epochs):
        model.train()
        total = 0.0
        for xb, yb in train_dl:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total += loss.item() * len(xb)
        history["train_loss"].append(total / max(1, len(train_idx)))

        model.eval()
        correct = 0
        with torch.no_grad():
            for xb, yb in val_dl:
                xb, yb = xb.to(device), yb.to(device)
                correct += (model(xb).argmax(1) == yb).sum().item()
        history["val_acc"].append(correct / max(1, len(val_idx)))

    return model, history
