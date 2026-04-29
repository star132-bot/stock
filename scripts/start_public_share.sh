#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

PORT="${1:-8130}"
HOST="127.0.0.1"
LOCAL_URL="http://${HOST}:${PORT}"
LOG_DIR="${PROJECT_ROOT}/.runtime"
TUNNEL_LOG="${LOG_DIR}/cloudflared.log"
TUNNEL_PID_FILE="${LOG_DIR}/cloudflared.pid"
PUBLIC_URL_FILE="${LOG_DIR}/public-share.url"

mkdir -p "$LOG_DIR"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed. Install it first with: brew install cloudflared"
  exit 1
fi

"${PROJECT_ROOT}/scripts/start_local_server.sh" "$PORT"

if [[ -f "$TUNNEL_PID_FILE" ]]; then
  EXISTING_PID="$(tr -d '\r\n' < "$TUNNEL_PID_FILE")"
  if [[ -n "$EXISTING_PID" ]] && kill -0 "$EXISTING_PID" >/dev/null 2>&1; then
    echo "Cloudflare tunnel already running. Check ${PUBLIC_URL_FILE}"
    exit 0
  fi
fi

rm -f "$PUBLIC_URL_FILE"

nohup cloudflared tunnel --url "$LOCAL_URL" --logfile "$TUNNEL_LOG" > /dev/null 2>&1 &
TUNNEL_PID=$!
disown "$TUNNEL_PID" >/dev/null 2>&1 || true
printf '%s\n' "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

for _ in {1..40}; do
  if [[ -f "$TUNNEL_LOG" ]]; then
    PUBLIC_URL="$(rg -o 'https://[-a-z0-9]+\.trycloudflare\.com' "$TUNNEL_LOG" | tail -n 1 || true)"
    if [[ -n "$PUBLIC_URL" ]]; then
      printf '%s\n' "$PUBLIC_URL" > "$PUBLIC_URL_FILE"
      echo "Public preview is ready at ${PUBLIC_URL}"
      exit 0
    fi
  fi

  if ! kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
    echo "cloudflared exited unexpectedly. See ${TUNNEL_LOG}"
    exit 1
  fi
  sleep 0.5
done

echo "Tunnel started but no public URL was captured yet. See ${TUNNEL_LOG}"
exit 1
