"""Ordre et (dé)quantification des angles phi/psi du beamforming compressé.

Décomposition de Givens d'une matrice de beamforming V (Nr x Nc) :
pour chaque colonne i = 1..min(Nc, Nr-1) on émet d'abord les angles phi
(rotation) puis les angles psi (élévation), dans l'ordre des lignes.

Exemple 4x4 -> phi_11, phi_21, phi_31, psi_21, psi_31, psi_41,
               phi_22, phi_32, psi_32, psi_42, phi_33, psi_43

Quantification (802.11ac) :
    phi in [0, 2*pi) sur b_phi bits :
        phi(k) = k * pi/2^(b_phi-1) + pi/2^b_phi
    psi in [0, pi/2) sur b_psi bits :
        psi(k) = k * pi/2^(b_psi+1) + pi/2^(b_psi+2)
"""

from __future__ import annotations

import math
from typing import Literal

AngleKind = Literal["phi", "psi"]


def angle_layout(nr: int, nc: int) -> list[tuple[AngleKind, int, int]]:
    """Ordre des angles (kind, ligne l, colonne i) pour une matrice Nr x Nc."""
    if nr < 2 or nc < 1 or nc > nr:
        raise ValueError(f"Dimensions invalides nr={nr}, nc={nc}")
    layout: list[tuple[AngleKind, int, int]] = []
    for i in range(1, min(nc, nr - 1) + 1):
        for l in range(i, nr):          # phi_{l,i}, l = i .. nr-1
            layout.append(("phi", l, i))
        for l in range(i + 1, nr + 1):  # psi_{l,i}, l = i+1 .. nr
            layout.append(("psi", l, i))
    return layout


def num_angles(nr: int, nc: int) -> tuple[int, int]:
    """Nombre d'angles (n_phi, n_psi) par sous-porteuse."""
    layout = angle_layout(nr, nc)
    n_phi = sum(1 for k, _, _ in layout if k == "phi")
    n_psi = sum(1 for k, _, _ in layout if k == "psi")
    return n_phi, n_psi


def dequantize_phi(k: int, b: int) -> float:
    return k * (math.pi / 2 ** (b - 1)) + (math.pi / 2 ** b)


def dequantize_psi(k: int, b: int) -> float:
    return k * (math.pi / 2 ** (b + 1)) + (math.pi / 2 ** (b + 2))


def quantize_phi(phi: float, b: int) -> int:
    k = round((phi - math.pi / 2 ** b) / (math.pi / 2 ** (b - 1)))
    return int(min(max(k, 0), 2 ** b - 1))


def quantize_psi(psi: float, b: int) -> int:
    k = round((psi - math.pi / 2 ** (b + 2)) / (math.pi / 2 ** (b + 1)))
    return int(min(max(k, 0), 2 ** b - 1))


def phi_step(b: int) -> float:
    """Pas de quantification de phi (tolérance de round-trip)."""
    return math.pi / 2 ** (b - 1)


def psi_step(b: int) -> float:
    return math.pi / 2 ** (b + 1)
