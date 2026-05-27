"""bfid - reproduction pédagogique du sensing Wi-Fi par Beamforming Feedback Information.

Ce paquet implémente la chaîne complète de reproduction de l'attaque "BFId"
(Todt, Morsbach, Strufe - KIT/KASTEL, ACM CCS '25) :

    capture (802.11ac/ax) -> parsing des angles BFI -> features -> modèle ML

Le code est conçu pour fonctionner SANS matériel radio (générateur de données
synthétiques) afin de valider toute la chaîne, puis sur de vraies captures.

USAGE ÉTHIQUE UNIQUEMENT : capture passive sur SON PROPRE réseau, avec le
consentement explicite des personnes présentes. Voir docs/ETHICS.md.
"""

from . import spec, angles, bitio, mimo_control, report

__all__ = ["spec", "angles", "bitio", "mimo_control", "report", "__version__"]
__version__ = "0.1.0"
