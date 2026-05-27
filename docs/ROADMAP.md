# Roadmap

État : ✅ fait · 🟡 partiel / à valider sur matériel · ⬜ à faire

## Phase 0 — Environnement
- ✅ Paquet Python `bfid`, tests, CLI (`python -m bfid`).
- ⬜ Vérifier la carte Wi-Fi en mode monitor sur la machine de capture.
- ⬜ Installer les outils système : `wireshark aircrack-ng tshark`.

## Phase 1 — Capture & parsing
- ✅ Tables 802.11ac (Ns, bits par angle), champ VHT MIMO Control.
- ✅ Parser du rapport VHT Compressed Beamforming (angles phi/psi).
- ✅ Encodeur symétrique (round-trip testé) → données synthétiques réalistes.
- ✅ Scripts de capture (`scripts/setup_monitor.sh`, `capture_bfi.sh`).
- 🟡 Lecteur pcap (`bfid/pcap.py`, scapy) : écrit mais **non validé sur de
  vraies trames**. À recouper avec Wi-BFI (convention d'ordre des bits, FCS,
  variantes de l'en-tête MAC).
- ⬜ Support HE (802.11ax) : champ HE MIMO Control (5 o), tables de
  sous-porteuses RU, bits d'angle HE.

## Phase 2 — Pipeline ML « à blanc »
- ✅ Extraction de features (stats par fenêtre) + fenêtres brutes pour CNN.
- ✅ Baseline scikit-learn (RandomForest) + validation croisée groupée.
- ✅ CNN temporel PyTorch (`bfid/model.py`, optionnel).
- ⬜ Reproduire les résultats publiés sur le dataset BeamSense (Hugging Face).
- ⬜ Loader pour le format BeamSense.

## Phase 3 — Collecte du dataset perso
- ✅ Protocole documenté (`docs/PROTOCOL.md`).
- ⬜ Script `label_from_journal.py` : pcap + journal CSV → `dataset.npz`.
- ⬜ Campagne de collecte (N personnes, M trajets, multi-jours).

## Phase 4 — Modèle perso
- ⬜ Entraînement CNN sur données réelles, courbes accuracy/loss.
- ⬜ Test sur session distincte (généralisation temporelle).
- ⬜ Comparaison BFI vs CSI si Nexmon disponible.

## Phase 5 — Reproduction fidèle BFId (optionnel)
- ⬜ Contacter les auteurs (KIT/KASTEL) pour le protocole/code exact.

## Dette technique connue
- `bfid/bitio.py` est bit-à-bit (lent en 80/160 MHz). Vectoriser via
  `numpy.unpackbits` pour le traitement de gros pcaps.
- `bfid/features.py` traite phi comme un réel ; encoder (sin, cos) pour gérer
  la circularité des angles sur de vraies données.
- Mapping SNR (`avg_snr_db`) approximatif ; affiner si besoin.
