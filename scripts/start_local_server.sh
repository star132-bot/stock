#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

PORT="${1:-8130}"
HOST="127.0.0.1"
LOG_DIR="${PROJECT_ROOT}/.runtime"
SERVER_LOG="${LOG_DIR}/local-server.log"
PID_FILE="${LOG_DIR}/local-server.pid"
URL_FILE="${LOG_DIR}/local-server.url"

mkdir -p "$LOG_DIR"

if curl -fsS --max-time 2 "http://${HOST}:${PORT}" >/dev/null 2>&1; then
  printf 'http://%s:%s\n' "$HOST" "$PORT" > "$URL_FILE"
  echo "Local preview is already available at http://${HOST}:${PORT}"
  exit 0
fi

if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(tr -d '\r\n' < "$PID_FILE")"
  if [[ -n "$EXISTING_PID" ]] && kill -0 "$EXISTING_PID" >/dev/null 2>&1; then
    echo "Local server already running at http://${HOST}:${PORT}"
    exit 0
  fi
fi

if lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port ${PORT} is already in use. Stop the existing service or use another port."
  exit 1
fi

if [[ -n "${HERMES_PYTHON_BIN:-}" ]] && [[ -x "${HERMES_PYTHON_BIN}" ]]; then
  PYTHON_BIN="${HERMES_PYTHON_BIN}"
elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

nohup "$PYTHON_BIN" -m uvicorn server:app --host "$HOST" --port "$PORT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!
disown "$SERVER_PID" >/dev/null 2>&1 || true

printf '%s\n' "$SERVER_PID" > "$PID_FILE"
printf 'http://%s:%s\n' "$HOST" "$PORT" > "$URL_FILE"

for _ in {1..20}; do
  if curl -fsS --max-time 2 "http://${HOST}:${PORT}" >/dev/null 2>&1; then
    echo "Local preview is running at http://${HOST}:${PORT}"
    exit 0
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    echo "Local server exited unexpectedly. See ${SERVER_LOG}"
    exit 1
  fi
  sleep 0.5
done

echo "Local server did not become ready in time. See ${SERVER_LOG}"
exit 1
