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

PYTHON_BIN=""
PYTHON_CANDIDATES=()
if [[ -n "${HERMES_PYTHON_BIN:-}" ]]; then
  PYTHON_CANDIDATES+=("${HERMES_PYTHON_BIN}")
fi
PYTHON_CANDIDATES+=("${PROJECT_ROOT}/.venv/bin/python")
for candidate in python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_CANDIDATES+=("$(command -v "$candidate")")
  fi
done

for candidate in "${PYTHON_CANDIDATES[@]}"; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3.10+ is required. Set HERMES_PYTHON_BIN or create .venv with Python 3.10+."
  exit 1
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
