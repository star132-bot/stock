#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR="${PROJECT_ROOT}/.runtime"
SERVER_PID_FILE="${LOG_DIR}/local-server.pid"
TUNNEL_PID_FILE="${LOG_DIR}/cloudflared.pid"

stop_pid_file() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 0
  fi

  local pid
  pid="$(tr -d '\r\n' < "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
  fi
  rm -f "$pid_file"
}

stop_pid_file "$TUNNEL_PID_FILE"
stop_pid_file "$SERVER_PID_FILE"

rm -f "${LOG_DIR}/public-share.url" "${LOG_DIR}/local-server.url"

echo "Stopped local preview and Cloudflare public share."
