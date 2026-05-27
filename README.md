# bfid — reproduction pédagogique du sensing Wi-Fi par BFI

Reproduction, à des fins **d'apprentissage et de recherche défensive**, de
l'attaque décrite dans :

> **BFId: Identity Inference Attacks Utilizing Beamforming Feedback
> Information** — Julian Todt, Felix Morsbach, Thorsten Strufe
> (KIT / KASTEL), ACM CCS '25. DOI
> [10.1145/3719027.3765062](https://dl.acm.org/doi/10.1145/3719027.3765062).

L'étude montre qu'on peut **ré-identifier une personne à ~99,5 %** à partir des
seules **Beamforming Feedback Information (BFI)** — des trames de gestion
802.11ac/ax diffusées **en clair** au niveau MAC, capturables passivement, sans
accès au réseau et sans que la cible porte d'appareil.

---

## ⚠️ Avant tout : éthique

Cette technique est une **capacité de surveillance**. Usage autorisé ici :
capture passive sur **votre propre réseau**, avec le **consentement explicite**
des personnes concernées, à des fins d'apprentissage. Tout le reste (réseaux de
tiers, personnes non consentantes, lieux publics, diffusion de données
biométriques) est exclu. **Lisez [`docs/ETHICS.md`](docs/ETHICS.md) — c'est une
condition d'usage du projet.**

---

## Ce que fait ce dépôt

Chaîne complète, conçue pour tourner **sans matériel radio** (générateur de
données synthétiques) puis sur de vraies captures :

```
capture 802.11  ->  parsing angles BFI  ->  features  ->  modèle ML  ->  identité
 (scripts/)         (bfid/report.py)      (features.py)  (baseline/model.py)
```

| Brique | Module | État |
|--------|--------|------|
| Tables & champ VHT MIMO Control | `bfid/spec.py`, `bfid/mimo_control.py` | ✅ |
| Parser/encodeur du rapport BFI (phi/psi) | `bfid/report.py`, `bfid/bitio.py`, `bfid/angles.py` | ✅ testé |
| Générateur de données synthétiques | `bfid/synthetic.py` | ✅ |
| Features + fenêtres temporelles | `bfid/features.py`, `bfid/dataset.py` | ✅ |
| Baseline scikit-learn (CV groupée) | `bfid/baseline.py` | ✅ runnable |
| CNN temporel PyTorch | `bfid/model.py` | ✅ (torch optionnel) |
| Lecteur pcap (scapy) | `bfid/pcap.py` | 🟡 à valider sur vrai pcap |
| Scripts de capture | `scripts/` | ✅ |

Détail et suite dans [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Installation

```bash
pip install -r requirements.txt        # coeur : numpy, scipy, scikit-learn
# optionnel :
pip install torch                      # CNN temporel (bfid/model.py)
pip install scapy                      # lecture de pcaps (bfid/pcap.py)
# système (capture réelle) :
sudo apt install wireshark aircrack-ng tshark
```

## Démarrage rapide (sans matériel)

```bash
# Aide-mémoire BFI + commandes de capture
python -m bfid info

# Pipeline complet sur données synthétiques (5 personnes)
python -m bfid demo --persons 5

# Générer puis évaluer un dataset
python -m bfid synth --persons 6 --out dataset.npz
python -m bfid train --data dataset.npz
```

`demo` doit afficher une accuracy nettement supérieure au hasard (~0.98 pour 5
personnes synthétiques), preuve que parsing → features → ML s'enchaînent.

## Capture réelle (Phase 1+, sur votre réseau)

```bash
sudo scripts/setup_monitor.sh wlan0 36 80MHz       # monitor + canal
sudo scripts/capture_bfi.sh wlan0mon capture.pcap 300
python -m bfid parse --pcap capture.pcap           # nécessite scapy
```

Le parser pcap doit être **recoupé avec [Wi-BFI](https://github.com/kfoysalhaque/Wi-BFI)**
sur de vraies trames (ordre des bits, FCS) avant d'y faire confiance.

## Tests

```bash
python -m pytest -q        # 36 tests, sans matériel ni torch
```

## Détails techniques

- **BFI** = angles phi (rotation) et psi (élévation) de la décomposition de
  Givens de la matrice de beamforming, **quantifiés** (2–9 bits selon
  SU/MU et codebook) et reportés **par sous-porteuse** (16 à 468 selon
  largeur et grouping). Voir `bfid/angles.py` et `bfid/spec.py`.
- Le **round-trip** encode→parse fait subir aux données synthétiques la vraie
  quantification 802.11ac : le parser est donc exercé de bout en bout.
- L'évaluation utilise une **validation croisée groupée par trajet**
  (`StratifiedGroupKFold`) pour éviter la fuite de données entre fenêtres d'un
  même enregistrement.

## Références

- Papier BFId (KIT) : https://publikationen.bibliothek.kit.edu/1000185756
- Wi-BFI : https://github.com/kfoysalhaque/Wi-BFI
- BeamSense (pipeline + dataset) : https://github.com/kfoysalhaque/BeamSense
- Dataset BeamSense (HF) : https://huggingface.co/datasets/foysalhaque/BeamSense
- Communiqué KIT : https://kastel-labs.de/news/wlan-als-spion-uberwachungsfalle-in-funknetzwerken/

## Licence / responsabilité

Code fourni à des fins éducatives. L'utilisateur est seul responsable du
respect des lois applicables et du cadre de [`docs/ETHICS.md`](docs/ETHICS.md).
