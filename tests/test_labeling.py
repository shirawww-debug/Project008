import numpy as np

from bfid import angles as A
from bfid.labeling import JournalEntry, assign_labels, read_journal
from bfid.report import CompressedBeamformingReport
from bfid.synthetic import DEFAULT_MIMO


def _make_report(seed: int) -> CompressedBeamformingReport:
    rng = np.random.default_rng(seed)
    ns = DEFAULT_MIMO.num_subcarriers
    n_phi, n_psi = A.num_angles(DEFAULT_MIMO.nr, DEFAULT_MIMO.nc)
    return CompressedBeamformingReport(
        DEFAULT_MIMO,
        np.zeros(DEFAULT_MIMO.nc, dtype=np.int8),
        rng.uniform(0, 6.0, size=(ns, n_phi)),
        rng.uniform(0, 1.5, size=(ns, n_psi)),
    )


def test_assign_labels_by_interval():
    # 3 rapports dans [0,10] -> alice ; 2 dans [20,30] -> bob ; 1 hors intervalle.
    reports = [
        (1.0, _make_report(1)), (5.0, _make_report(2)), (9.0, _make_report(3)),
        (15.0, _make_report(4)),                      # ignoré (hors journal)
        (22.0, _make_report(5)), (28.0, _make_report(6)),
    ]
    journal = [
        JournalEntry(0.0, 10.0, "alice"),
        JournalEntry(20.0, 30.0, "bob"),
    ]
    samples = assign_labels(reports, journal)
    assert len(samples) == 2
    by_person = {s.person: s for s in samples}
    assert by_person["alice"].n_frames == 3
    assert by_person["bob"].n_frames == 2
    # labels entiers stables (ordre alphabétique)
    assert by_person["alice"].label == 0
    assert by_person["bob"].label == 1


def test_empty_interval_skipped():
    reports = [(1.0, _make_report(1))]
    journal = [JournalEntry(0.0, 5.0, "a"), JournalEntry(100.0, 200.0, "b")]
    samples = assign_labels(reports, journal)
    assert {s.person for s in samples} == {"a"}


def test_read_journal(tmp_path):
    path = tmp_path / "journal.csv"
    path.write_text("t_debut,t_fin,label\n0.0,10.0,alice\n20,30,bob\n")
    entries = read_journal(str(path))
    assert len(entries) == 2
    assert entries[0].label == "alice" and entries[0].t_end == 10.0


def test_read_journal_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("start,end,who\n0,1,x\n")
    try:
        read_journal(str(path))
    except ValueError:
        return
    raise AssertionError("colonnes manquantes non détectées")
