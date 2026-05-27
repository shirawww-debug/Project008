#!/usr/bin/env bash
# Capture les trames Action 802.11 (qui portent les rapports BFI) vers un pcap.
#
# Usage : sudo scripts/capture_bfi.sh <iface_monitor> <sortie.pcap> [duree_s]
#   ex.  : sudo scripts/capture_bfi.sh wlan0mon capture.pcap 300
#
# Le filtre ne garde que les Action / Action No Ack (subtype 13 et 14), où se
# trouvent les VHT/HE Compressed Beamforming Report. Décodez ensuite avec :
#   python -m bfid parse --pcap capture.pcap
#
# ⚠️  ÉTHIQUE : votre réseau, avec consentement. Voir docs/ETHICS.md.
set -euo pipefail

IFACE="${1:?Usage: capture_bfi.sh <iface_monitor> <sortie.pcap> [duree_s]}"
OUT="${2:?fichier pcap de sortie requis}"
DURATION="${3:-300}"

if [[ $EUID -ne 0 ]]; then
  echo "Ce script doit être lancé en root (sudo)." >&2
  exit 1
fi

# Filtre de capture : type management (0) + subtype Action (13) ou Action NoAck (14).
# wlan[0] = octet Frame Control ; 0xD0 = Action, 0xE0 = Action No Ack.
FILTER='(wlan[0] == 0xd0) or (wlan[0] == 0xe0)'

echo "[*] Capture ${DURATION}s sur ${IFACE} -> ${OUT}"
echo "    filtre : ${FILTER}"

if command -v tshark >/dev/null 2>&1; then
  tshark -i "${IFACE}" -a "duration:${DURATION}" \
    -f "${FILTER}" -w "${OUT}"
else
  echo "[!] tshark introuvable, fallback tcpdump"
  timeout "${DURATION}" tcpdump -i "${IFACE}" -w "${OUT}" "${FILTER}"
fi

echo "[+] Capture terminée : ${OUT}"
echo "    Analyse : python -m bfid parse --pcap ${OUT}"
