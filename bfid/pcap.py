"""Lecture de captures pcap et extraction des rapports BFI (scapy, optionnel).

Chaîne réelle : la carte en mode monitor capture des trames Action 802.11
(subtype 13 = Action, 14 = Action No Ack) ; on isole le corps de la trame de
gestion, puis on le décode via report.parse_action_body.

scapy est une dépendance OPTIONNELLE (import paresseux). Sans capture réelle
sous la main, on ne peut pas valider ce module ici : il doit être recoupé avec
Wi-BFI (https://github.com/kfoysalhaque/Wi-BFI) sur de vrais pcaps, notamment
la convention d'ordre des bits et la présence éventuelle d'un FCS. Voir
docs/ROADMAP.md.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterator

import numpy as np

from .dataset import BfiSample
from .report import CompressedBeamformingReport, parse_action_body

_MGMT_TYPE = 0
_ACTION_SUBTYPES = {13, 14}
_DOT11_MGMT_HEADER_LEN = 24


def _require_scapy():
    try:
        from scapy.all import Dot11, RadioTap, rdpcap  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "scapy requis pour lire les pcaps : pip install scapy"
        ) from exc
    from scapy.all import Dot11, rdpcap
    return Dot11, rdpcap


def iter_reports(
    pcap_path: str, has_fcs: bool = True
) -> Iterator[tuple[float, str, CompressedBeamformingReport]]:
    """Itère sur (timestamp, source MAC, rapport) des trames BFI d'un pcap."""
    Dot11, rdpcap = _require_scapy()
    for pkt in rdpcap(pcap_path):
        if not pkt.haslayer(Dot11):
            continue
        dot11 = pkt[Dot11]
        if dot11.type != _MGMT_TYPE or dot11.subtype not in _ACTION_SUBTYPES:
            continue
        raw = bytes(dot11)
        body = raw[_DOT11_MGMT_HEADER_LEN:]
        if has_fcs and len(body) > 4:
            body = body[:-4]
        try:
            report = parse_action_body(body)
        except (ValueError, EOFError, IndexError):
            continue
        ts = float(getattr(pkt, "time", 0.0))
        src = getattr(dot11, "addr2", "") or ""
        yield ts, src, report


def reports_to_samples(
    reports: list[tuple[float, str, CompressedBeamformingReport]],
    label_by_mac: dict[str, int] | None = None,
) -> list[BfiSample]:
    """Regroupe les rapports par MAC source en traces (un BfiSample par MAC).

    `label_by_mac` mappe une adresse MAC vers un id de personne. Dans la vraie
    attaque, le label provient du protocole de collecte étiqueté (qui marchait
    quand), PAS de la MAC : voir docs/PROTOCOL.md. Cette agrégation par MAC
    n'est qu'un point de départ pratique.
    """
    by_src: dict[str, list[CompressedBeamformingReport]] = defaultdict(list)
    for _, src, rep in sorted(reports, key=lambda r: r[0]):
        by_src[src].append(rep)

    samples = []
    for src, reps in by_src.items():
        phi = np.stack([r.phi for r in reps], axis=0)
        psi = np.stack([r.psi for r in reps], axis=0)
        label = (label_by_mac or {}).get(src, 0)
        samples.append(BfiSample(phi=phi, psi=psi, label=label,
                                 person=src, meta={"source": "pcap"}))
    return samples
