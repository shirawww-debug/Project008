"""Générateur de données BFI synthétiques.

Objectif : valider toute la chaîne (parsing -> features -> ML) SANS matériel
radio ni personnes réelles. Ce n'est PAS un simulateur de propagation : c'est
un modèle jouet où chaque "personne" imprime une signature reproductible et
distincte sur les angles du canal, plus du bruit et une dérive temporelle
(mouvement). Cela suffit à exercer et tester le pipeline de bout en bout.

Optionnellement (roundtrip=True, défaut), chaque trame passe par
encode_report -> parse_action_body, ce qui fait subir aux angles la VRAIE
quantification 802.11ac et valide le parser sur des octets réalistes.
"""

from __future__ import annotations

import math

import numpy as np

from . import angles as A
from .dataset import BfiSample
from .mimo_control import VhtMimoControl
from .report import CompressedBeamformingReport, build_action_body, parse_action_body

# Config par défaut : 20 MHz, Ng=4 -> 16 sous-porteuses, matrice 2x1.
# Petit et rapide, suffisant pour les tests et la démo.
DEFAULT_MIMO = VhtMimoControl(
    nc=1, nr=2, channel_width=0, grouping=2, codebook=1, feedback_type=0
)

PHI_MAX = 2 * math.pi
PSI_MAX = math.pi / 2


def _person_signature(rng: np.random.Generator, ns: int, n_phi: int, n_psi: int):
    """Décalage moyen, lisse selon les sous-porteuses, propre à une personne."""
    # Profil basse fréquence le long des sous-porteuses (corps = perturbation
    # spatialement corrélée du canal).
    freqs = rng.uniform(0.5, 2.5, size=3)
    phases = rng.uniform(0, 2 * math.pi, size=3)
    x = np.linspace(0, 1, ns)[:, None]
    basis = sum(
        rng.uniform(-1, 1) * np.sin(2 * math.pi * f * x + p)
        for f, p in zip(freqs, phases)
    )  # (ns, 1)
    phi_amp = rng.uniform(0.15, 0.35) * PHI_MAX
    psi_amp = rng.uniform(0.15, 0.35) * PSI_MAX
    phi_off = phi_amp * basis * rng.uniform(-1, 1, size=(1, n_phi))
    psi_off = psi_amp * basis * rng.uniform(-1, 1, size=(1, n_psi))
    return phi_off, psi_off


def generate_sample(
    label: int,
    person: str,
    n_frames: int = 200,
    mimo: VhtMimoControl = DEFAULT_MIMO,
    noise: float = 0.04,
    drift: float = 0.01,
    seed: int = 0,
    roundtrip: bool = True,
) -> BfiSample:
    """Génère une trace BFI pour une personne (signature déterministe via seed)."""
    ns = mimo.num_subcarriers
    n_phi, n_psi = A.num_angles(mimo.nr, mimo.nc)

    sig_rng = np.random.default_rng(1000 + label)        # signature stable / personne
    dyn_rng = np.random.default_rng(seed * 100003 + label)  # dynamique / trace

    phi_off, psi_off = _person_signature(sig_rng, ns, n_phi, n_psi)
    phi_base = 0.5 * PHI_MAX + phi_off
    psi_base = 0.5 * PSI_MAX + psi_off

    phi_seq = np.empty((n_frames, ns, n_phi))
    psi_seq = np.empty((n_frames, ns, n_psi))

    phi_walk = np.zeros((ns, n_phi))
    psi_walk = np.zeros((ns, n_psi))
    for t in range(n_frames):
        phi_walk += drift * PHI_MAX * dyn_rng.normal(size=(ns, n_phi))
        psi_walk += drift * PSI_MAX * dyn_rng.normal(size=(ns, n_psi))
        phi = phi_base + phi_walk + noise * PHI_MAX * dyn_rng.normal(size=(ns, n_phi))
        psi = psi_base + psi_walk + noise * PSI_MAX * dyn_rng.normal(size=(ns, n_psi))
        phi_seq[t] = np.clip(phi, 0, PHI_MAX - 1e-6)
        psi_seq[t] = np.clip(psi, 0, PSI_MAX - 1e-6)

    if roundtrip:
        snr = np.full(mimo.nc, 40, dtype=np.int8)
        for t in range(n_frames):
            rep = CompressedBeamformingReport(mimo, snr, phi_seq[t], psi_seq[t])
            decoded = parse_action_body(build_action_body(rep))
            phi_seq[t] = decoded.phi
            psi_seq[t] = decoded.psi

    return BfiSample(phi=phi_seq, psi=psi_seq, label=label, person=person,
                     meta={"synthetic": True, "seed": seed})


def generate_dataset(
    n_persons: int = 4,
    traces_per_person: int = 6,
    n_frames: int = 200,
    mimo: VhtMimoControl = DEFAULT_MIMO,
    roundtrip: bool = True,
    seed: int = 0,
) -> list[BfiSample]:
    """Génère un dataset multi-personnes, plusieurs traces chacune."""
    samples: list[BfiSample] = []
    for label in range(n_persons):
        for trace in range(traces_per_person):
            samples.append(
                generate_sample(
                    label=label,
                    person=f"person_{label}",
                    n_frames=n_frames,
                    mimo=mimo,
                    seed=seed * 1000 + trace,
                    roundtrip=roundtrip,
                )
            )
    return samples
