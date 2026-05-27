"""Constantes issues de la norme IEEE 802.11ac (VHT Compressed Beamforming).

Références : IEEE Std 802.11ac-2013, section "VHT Compressed Beamforming
Report field" et tables associées (nombre de sous-porteuses Ns, nombre de
bits par angle selon le codebook).

Le 802.11ax (HE) réutilise le même principe d'angles phi/psi compressés mais
avec un champ de contrôle différent (5 octets) et d'autres tables de
sous-porteuses (RU-based). Il est documenté ici comme extension future ;
l'implémentation de référence reste VHT.
"""

from __future__ import annotations

# Channel Width (champ 2 bits du VHT MIMO Control) -> largeur en MHz.
# La valeur 3 couvre 160 MHz et 80+80 MHz ; on la traite comme 160.
CHANNEL_WIDTH_MHZ = {0: 20, 1: 40, 2: 80, 3: 160}

# Grouping Ng (champ 2 bits) -> nombre de sous-porteuses regroupées.
# La valeur 3 est réservée en 802.11ac.
GROUPING_NG = {0: 1, 1: 2, 2: 4}

# Ns : nombre de sous-porteuses présentes dans le rapport, indexé par
# (largeur en MHz, Ng). Valeurs normatives 802.11ac.
NS_TABLE = {
    (20, 1): 52,  (20, 2): 30,  (20, 4): 16,
    (40, 1): 108, (40, 2): 58,  (40, 4): 30,
    (80, 1): 234, (80, 2): 122, (80, 4): 62,
    (160, 1): 468, (160, 2): 244, (160, 4): 124,
}

# Nombre de bits de quantification (b_psi, b_phi) selon le type de feedback
# (SU/MU) et le bit "Codebook Information".
BIT_TABLE = {
    ("SU", 0): (2, 4),
    ("SU", 1): (4, 6),
    ("MU", 0): (5, 7),
    ("MU", 1): (7, 9),
}

# Codes de l'Action frame VHT portant le rapport de beamforming.
CATEGORY_VHT = 21
VHT_ACTION_COMPRESSED_BEAMFORMING = 0


def num_subcarriers(width_mhz: int, ng: int) -> int:
    """Nombre de sous-porteuses Ns pour une largeur et un grouping donnés."""
    try:
        return NS_TABLE[(width_mhz, ng)]
    except KeyError as exc:
        raise ValueError(f"Combinaison (width={width_mhz}MHz, Ng={ng}) invalide") from exc


def angle_bits(feedback_name: str, codebook: int) -> tuple[int, int]:
    """Renvoie (b_psi, b_phi) pour un type de feedback et un codebook."""
    try:
        return BIT_TABLE[(feedback_name, codebook)]
    except KeyError as exc:
        raise ValueError(f"Combinaison (feedback={feedback_name}, codebook={codebook}) invalide") from exc
