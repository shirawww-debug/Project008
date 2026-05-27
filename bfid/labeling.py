"""Étiquetage : transformer une capture + un journal en dataset entraînable.

Les BFI n'identifient pas la classe par elles-mêmes : on connaît le label
parce qu'on contrôle *qui/quoi est où, quand* (voir docs/PROTOCOL.md). Le
journal d'étiquetage est un CSV décrivant des intervalles temporels :

    t_debut,t_fin,label
    1716800000.0,1716800030.0,person_0
    1716800035.0,1716800065.0,person_1

Chaque rapport BFI capté (avec son timestamp) est rattaché à l'intervalle qui
le contient, et tous les rapports d'un même intervalle forment un BfiSample
(une "trace"). Les labels texte sont mappés vers des entiers stables.

La logique d'assignation (`assign_labels`) est séparée de la lecture pcap
(scapy) pour être testable sans matériel ni dépendance optionnelle.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass

import numpy as np

from .dataset import BfiSample
from .report import CompressedBeamformingReport


@dataclass
class JournalEntry:
    t_start: float
    t_end: float
    label: str


def read_journal(csv_path: str) -> list[JournalEntry]:
    """Lit un journal CSV (colonnes t_debut, t_fin, label)."""
    entries: list[JournalEntry] = []
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"t_debut", "t_fin", "label"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(
                f"Le journal doit avoir les colonnes {sorted(required)}, "
                f"trouvé {reader.fieldnames}"
            )
        for row in reader:
            entries.append(JournalEntry(
                t_start=float(row["t_debut"]),
                t_end=float(row["t_fin"]),
                label=row["label"].strip(),
            ))
    return entries


def assign_labels(
    reports: list[tuple[float, CompressedBeamformingReport]],
    journal: list[JournalEntry],
) -> list[BfiSample]:
    """Rattache chaque rapport à l'intervalle qui le contient -> BfiSamples.

    Un BfiSample par entrée de journal (= une trace). Les rapports hors de
    tout intervalle sont ignorés. Les labels texte deviennent des entiers
    stables (ordre alphabétique) pour la classification.
    """
    label_names = sorted({e.label for e in journal})
    label_to_int = {name: i for i, name in enumerate(label_names)}

    ordered = sorted(reports, key=lambda r: r[0])
    samples: list[BfiSample] = []
    for entry in journal:
        reps = [
            rep for ts, rep in ordered
            if entry.t_start <= ts <= entry.t_end
        ]
        if not reps:
            continue
        phi = np.stack([r.phi for r in reps], axis=0)
        psi = np.stack([r.psi for r in reps], axis=0)
        samples.append(BfiSample(
            phi=phi, psi=psi,
            label=label_to_int[entry.label], person=entry.label,
            meta={"source": "pcap+journal", "n_reports": len(reps)},
        ))
    return samples


def label_from_journal(
    pcap_path: str, journal_csv: str, has_fcs: bool = True
) -> list[BfiSample]:
    """pcap + journal CSV -> liste de BfiSample (nécessite scapy)."""
    from .pcap import iter_reports  # import paresseux

    journal = read_journal(journal_csv)
    reports = [(ts, rep) for ts, _src, rep in iter_reports(pcap_path, has_fcs=has_fcs)]
    return assign_labels(reports, journal)
