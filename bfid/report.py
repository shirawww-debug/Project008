"""Rapport VHT Compressed Beamforming : parsing et (ré)encodage.

Structure du champ "VHT Compressed Beamforming Report" :
    1. Average SNR : Nc octets signés (un par flux spatial).
    2. Matrice de beamforming compressée : pour chaque sous-porteuse, les
       angles phi/psi empilés dans l'ordre donné par `angles.angle_layout`.

L'Action frame complète qui le transporte :
    Category (=21) | VHT Action (=0) | VHT MIMO Control (3o) | Report [ | MU report ]

On ne décode pas le "MU Exclusive Beamforming Report" (delta SNR MU) : il
n'apporte pas d'information de signature corporelle exploitable pour le
sensing, et sa longueur dépend du contexte sounding.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import angles as A
from . import spec
from .bitio import BitReader, BitWriter
from .mimo_control import VhtMimoControl, pack_mimo_control, parse_mimo_control


@dataclass
class CompressedBeamformingReport:
    mimo: VhtMimoControl
    avg_snr_raw: np.ndarray   # (nc,) int8 brut
    phi: np.ndarray           # (ns, n_phi) radians
    psi: np.ndarray           # (ns, n_psi) radians

    @property
    def avg_snr_db(self) -> np.ndarray:
        # Mapping approximatif : la norme code le SNR sur 8 bits signés par
        # pas de 0.25 dB. Le SNR n'est pas central pour la signature BFI.
        return self.avg_snr_raw.astype(float) * 0.25

    @property
    def num_subcarriers(self) -> int:
        return self.phi.shape[0]


def parse_report(payload: bytes, mimo: VhtMimoControl) -> CompressedBeamformingReport:
    """Décode le champ report (octets APRÈS le VHT MIMO Control)."""
    nc, nr, ns = mimo.nc, mimo.nr, mimo.num_subcarriers
    b_psi, b_phi = mimo.bits_psi_phi

    avg_snr_raw = np.frombuffer(payload[:nc], dtype=np.int8).copy()
    if avg_snr_raw.size != nc:
        raise ValueError("Payload trop court pour le champ Average SNR")

    layout = A.angle_layout(nr, nc)
    n_phi, n_psi = A.num_angles(nr, nc)
    phi = np.zeros((ns, n_phi), dtype=float)
    psi = np.zeros((ns, n_psi), dtype=float)

    reader = BitReader(payload[nc:])
    for s in range(ns):
        pi = si = 0
        for kind, _, _ in layout:
            if kind == "phi":
                phi[s, pi] = A.dequantize_phi(reader.read(b_phi), b_phi)
                pi += 1
            else:
                psi[s, si] = A.dequantize_psi(reader.read(b_psi), b_psi)
                si += 1
    return CompressedBeamformingReport(mimo, avg_snr_raw, phi, psi)


def encode_report(report: CompressedBeamformingReport) -> bytes:
    """Ré-encode un rapport en octets (utilisé par le générateur synthétique)."""
    mimo = report.mimo
    b_psi, b_phi = mimo.bits_psi_phi
    layout = A.angle_layout(mimo.nr, mimo.nc)
    ns = mimo.num_subcarriers

    out = bytearray(report.avg_snr_raw.astype(np.int8).tobytes())
    writer = BitWriter()
    for s in range(ns):
        pi = si = 0
        for kind, _, _ in layout:
            if kind == "phi":
                writer.write(A.quantize_phi(report.phi[s, pi], b_phi), b_phi)
                pi += 1
            else:
                writer.write(A.quantize_psi(report.psi[s, si], b_psi), b_psi)
                si += 1
    out += writer.to_bytes()
    return bytes(out)


def parse_action_body(body: bytes) -> CompressedBeamformingReport:
    """Décode le corps d'une Action frame VHT Compressed Beamforming."""
    if len(body) < 5:
        raise ValueError("Corps d'Action frame trop court")
    category, action = body[0], body[1]
    if category != spec.CATEGORY_VHT or action != spec.VHT_ACTION_COMPRESSED_BEAMFORMING:
        raise ValueError(
            f"Pas une trame VHT Compressed Beamforming "
            f"(category={category}, action={action})"
        )
    mimo = parse_mimo_control(body[2:5])
    return parse_report(body[5:], mimo)


def build_action_body(report: CompressedBeamformingReport) -> bytes:
    """Construit le corps d'une Action frame VHT à partir d'un rapport."""
    return (
        bytes([spec.CATEGORY_VHT, spec.VHT_ACTION_COMPRESSED_BEAMFORMING])
        + pack_mimo_control(report.mimo)
        + encode_report(report)
    )
