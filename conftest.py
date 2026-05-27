"""Permet `import bfid` quand pytest tourne depuis la racine du dépôt."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
