# Protocole de collecte du dataset (Phase 3)

> Préalable : lire et respecter `docs/ETHICS.md`. Recueillir le consentement
> écrit de chaque participant avant toute collecte.

## Principe

L'attaque BFId est un apprentissage **supervisé** : le modèle apprend à
reconnaître un ensemble **fermé** de personnes vues à l'entraînement. Il ne
peut pas identifier un inconnu. La qualité du dataset détermine tout.

La difficulté centrale est l'**étiquetage** : associer chaque intervalle de
trames BFI à la bonne personne. Les BFI n'identifient pas la personne par
elles-mêmes — on connaît le label parce qu'on contrôle *qui marche quand*.

## Matériel

- 1 station d'écoute Linux + carte monitor (Alfa AWUS036ACM / Intel AX200…).
- 1 box Wi-Fi 5/6 avec beamforming actif.
- ≥ 1 client connecté générant du trafic (un smartphone qui streame suffit à
  provoquer des soundings réguliers → flux de BFI).

## Variables à contrôler

| Variable            | Recommandation                                        |
|---------------------|-------------------------------------------------------|
| Position box/écoute | Fixes pendant toute la campagne.                      |
| Canal / largeur     | Fixes (ex. canal 36, 80 MHz).                         |
| Personnes (N)       | Vous + cohabitants consentants.                       |
| Trajets / personne  | M ≥ 8–10, variés (angles, vitesses, trajectoires).    |
| Durée / trajet      | Fixe (ex. 20–30 s), une seule personne à la fois.     |
| Pièce vide          | Enregistrer aussi une classe « vide » (référence).    |

## Déroulé d'une session

1. `sudo scripts/setup_monitor.sh wlan0 36 80MHz`
2. Vérifier le flux BFI : `scripts/capture_bfi.sh wlan0mon test.pcap 30`
   puis `python -m bfid parse --pcap test.pcap` (doit lister des rapports).
3. Pour chaque personne, pour chaque trajet :
   - Noter `t_début` (horodatage), l'ID personne, le type de trajet.
   - La personne (et elle seule) marche dans la pièce le temps imparti.
   - Noter `t_fin`.
4. Tenir un **journal d'étiquetage** : CSV `pcap, t_debut, t_fin, person_id`.

## Étiquetage et conversion

L'agrégation par adresse MAC (`bfid.pcap.reports_to_samples`) ne suffit PAS à
étiqueter par personne : tous les soundings d'un même client partagent la même
MAC quelle que soit la personne dans la pièce. Le label vient du **journal**
(intervalles temporels). Procédure :

1. Parser le pcap en (timestamp, rapport).
2. Découper par intervalle `[t_debut, t_fin]` du journal → assigner `person_id`.
3. Construire des `BfiSample` (un par trajet) et `save_samples(...)`.

> TODO outillage : un script `label_from_journal.py` (pcap + CSV → dataset.npz)
> est listé dans `docs/ROADMAP.md`.

## Bonnes pratiques anti-fuite

- Ne jamais mélanger les fenêtres d'un même trajet entre train et test :
  l'évaluation utilise une **validation croisée groupée par trajet**
  (`StratifiedGroupKFold`, voir `bfid/baseline.py`).
- Collecter sur **plusieurs jours** : un modèle qui ne marche que le jour de
  collecte sur-apprend les conditions du canal, pas la personne.
- Garder un **jeu de test** issu d'une session distincte.
