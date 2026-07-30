#!/bin/zsh
# Double-click this file to put the Cash Memer website online.
# It starts a local web server + a free Cloudflare tunnel and prints the public link.
#
# The site lives in the "docs" folder next to this file.
# For the public link you need cloudflared. Either drop the binary beside this
# file, or install it once with:  brew install cloudflared
cd "$(dirname "$0")"

SITE_DIR="docs"
PORT=8901

if [ ! -d "$SITE_DIR" ]; then
  echo "Could not find the '$SITE_DIR' folder next to this script."
  echo "Run this from the root of the Cash-Meter repository."
  exit 1
fi

echo "Starting Cash Memer website server..."
python3 -m http.server "$PORT" --directory "$SITE_DIR" --bind 0.0.0.0 >/dev/null 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT INT TERM
sleep 1

LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "unavailable")

echo ""
echo "Local (this Mac):      http://localhost:$PORT"
echo "Same Wi-Fi devices:    http://$LAN_IP:$PORT"
echo ""

if [ -x "./cloudflared" ]; then
  CF="./cloudflared"
elif command -v cloudflared >/dev/null 2>&1; then
  CF="cloudflared"
else
  echo "cloudflared not found — serving locally only."
  echo "For a public link: brew install cloudflared, then run this again."
  echo "Press Ctrl+C to stop."
  wait $SERVER_PID
  exit 0
fi

echo "Creating public link (any device, any network)..."
echo "Look for the https://....trycloudflare.com line below — that's your shareable URL."
echo "Keep this window open while sharing. Press Ctrl+C to stop."
echo ""

"$CF" tunnel --url "http://localhost:$PORT"
