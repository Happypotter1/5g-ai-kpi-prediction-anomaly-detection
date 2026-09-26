#!/bin/bash
set -u

OUT_DIR="$HOME/5g-week2/pcap"
mkdir -p "$OUT_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
NAME="${1:-5g_capture_${TIMESTAMP}}"
OUT_FILE="${OUT_DIR}/${NAME}.pcap"

echo "=============================================="
echo "        5G Network Data Capture Tool"
echo "=============================================="

command -v tcpdump >/dev/null 2>&1 || { echo "[ERROR] tcpdump is not installed."; exit 1; }
sudo ip netns list | grep -q '^ueransim' || { echo "[ERROR] namespace 'ueransim' does not exist."; exit 1; }

for pattern in '/bin/amf' '/bin/upf' 'nr-gnb' 'nr-ue'; do
    if pgrep -f "$pattern" >/dev/null; then echo "[OK] $pattern"; else echo "[WARN] $pattern not running"; fi
done

echo "Output: $OUT_FILE"
echo "N2=SCTP/38412, N3=UDP/2152, user plane=ICMP"
echo "Press Ctrl+C to stop."

START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
sudo tcpdump -i any -s 0 -nn -U -w "$OUT_FILE" 'sctp port 38412 or udp port 2152 or icmp'
END_TIME=$(date +"%Y-%m-%d %H:%M:%S")

echo "Start: $START_TIME"
echo "End:   $END_TIME"
echo "Saved: $OUT_FILE"

PACKETS=$(sudo tcpdump -nn -r "$OUT_FILE" 2>/dev/null | wc -l)
SCTP_COUNT=$(sudo tcpdump -nn -r "$OUT_FILE" 'sctp port 38412' 2>/dev/null | wc -l)
GTP_COUNT=$(sudo tcpdump -nn -r "$OUT_FILE" 'udp port 2152' 2>/dev/null | wc -l)
ICMP_COUNT=$(sudo tcpdump -nn -r "$OUT_FILE" 'icmp' 2>/dev/null | wc -l)
echo "Total packets : $PACKETS"
echo "N2/SCTP       : $SCTP_COUNT"
echo "N3/GTP-U      : $GTP_COUNT"
echo "ICMP          : $ICMP_COUNT"

