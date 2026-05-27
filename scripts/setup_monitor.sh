#!/usr/bin/env bash
# Met une carte Wi-Fi en mode monitor et la cale sur un canal/largeur.
#
# Usage : sudo scripts/setup_monitor.sh <iface> <canal> [largeur]
#   ex.  : sudo scripts/setup_monitor.sh wlan0 36 80MHz
#
# ⚠️  ÉTHIQUE : à n'utiliser que sur VOTRE réseau, avec le consentement des
#     personnes présentes. Voir docs/ETHICS.md.
set -euo pipefail

IFACE="${1:?Usage: setup_monitor.sh <iface> <canal> [largeur]}"
CHANNEL="${2:?canal requis (ex. 36)}"
WIDTH="${3:-80MHz}"

if [[ $EUID -ne 0 ]]; then
  echo "Ce script doit être lancé en root (sudo)." >&2
  exit 1
fi

echo "[*] Arrêt des processus susceptibles d'interférer (NetworkManager...)"
airmon-ng check kill || true

echo "[*] Passage de ${IFACE} en mode monitor"
airmon-ng start "${IFACE}" >/dev/null

MON_IFACE="${IFACE}"
if ip link show "${IFACE}mon" >/dev/null 2>&1; then
  MON_IFACE="${IFACE}mon"
fi

echo "[*] Réglage du canal ${CHANNEL} (${WIDTH}) sur ${MON_IFACE}"
iw dev "${MON_IFACE}" set channel "${CHANNEL}" "${WIDTH}"

echo "[+] Interface monitor prête : ${MON_IFACE}"
echo "    Vérifiez les trames BFI : scripts/capture_bfi.sh ${MON_IFACE} capture.pcap 60"
