#!/bin/sh
# Serve the Cash Memer website and print both links:
#   - localhost, for this machine
#   - the LAN IP, for phones and tablets on the same Wi-Fi
#
# Usage:  ./serve.sh [port]        (default port 8901)
# Works on macOS and Linux. Stop it with Ctrl+C.

cd "$(dirname "$0")" || exit 1

SITE_DIR="website"
PORT="${1:-8901}"

if [ ! -d "$SITE_DIR" ]; then
  echo "No '$SITE_DIR' folder here. Run this from the repository root."
  exit 1
fi

# First non-loopback IPv4 address, however this system likes to report it.
lan_ip() {
  ipconfig getifaddr en0 2>/dev/null && return          # macOS, Wi-Fi
  ipconfig getifaddr en1 2>/dev/null && return          # macOS, second adapter
  hostname -I 2>/dev/null | awk '{print $1}' | grep . && return   # most Linux
  ip -4 addr show scope global 2>/dev/null \
    | awk '/inet /{sub(/\/.*/,"",$2); print $2; exit}' | grep . && return
  echo ""
}

IP="$(lan_ip)"

echo ""
echo "  Cash Memer — serving ./$SITE_DIR"
echo "  ----------------------------------------"
echo "  Localhost:   http://localhost:$PORT"
if [ -n "$IP" ]; then
  echo "  Network IP:  http://$IP:$PORT"
  echo ""
  echo "  Open the Network IP link on your phone or tablet"
  echo "  while it's on the same Wi-Fi as this machine."
else
  echo "  Network IP:  (could not detect one — are you online?)"
fi
echo ""
echo "  Press Ctrl+C to stop."
echo ""

# --bind 0.0.0.0 is what makes the IP link reachable from other devices.
exec python3 -m http.server "$PORT" --directory "$SITE_DIR" --bind 0.0.0.0
