"""Interface web (Flask) pour tester le pipeline BFI.

L'app se lance avec :  python -m bfid web   (ou  flask --app bfid.web.app run)

⚠️ Outil local : par défaut sur 127.0.0.1. Capture passive sur SON réseau,
avec consentement. Voir docs/ETHICS.md.
"""

from .app import create_app

__all__ = ["create_app"]
