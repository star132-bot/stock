#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR="${PROJECT_ROOT}/.runtime"
LOCAL_URL_FILE="${LOG_DIR}/local-server.url"
PUBLIC_URL_FILE="${LOG_DIR}/public-share.url"
SERVER_PID_FILE="${LOG_DIR}/local-server.pid"
TUNNEL_PID_FILE="${LOG_DIR}/cloudflared.pid"

read_file_if_exists() {
  local path="$1"
  if [[ -f "$path" ]]; then
    tr -d '\r\n' < "$path"
  fi
}

pid_running() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi

  local pid
  pid="$(tr -d '\r\n' < "$pid_file")"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

LOCAL_URL="$(read_file_if_exists "$LOCAL_URL_FILE")"
PUBLIC_URL="$(read_file_if_exists "$PUBLIC_URL_FILE")"

if [[ -n "$LOCAL_URL" ]]; then
  echo "Local URL: ${LOCAL_URL}"
else
  echo "Local URL: not found"
fi

if [[ -n "$PUBLIC_URL" ]]; then
  echo "Public URL: ${PUBLIC_URL}"
else
  echo "Public URL: not found"
fi

if pid_running "$SERVER_PID_FILE"; then
  echo "Local Server: running"
else
  echo "Local Server: stopped or unmanaged"
fi

if pid_running "$TUNNEL_PID_FILE"; then
  echo "Cloudflare Tunnel: running"
else
  echo "Cloudflare Tunnel: stopped or unmanaged"
fi

if [[ -f "${LOG_DIR}/cloudflared.log" ]]; then
  echo "Tunnel Log: ${LOG_DIR}/cloudflared.log"
fi
