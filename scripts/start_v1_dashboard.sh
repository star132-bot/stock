#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

bash "${PROJECT_ROOT}/scripts/start_local_server.sh"

LOCAL_URL_FILE="${PROJECT_ROOT}/.runtime/local-server.url"
if [[ -f "${LOCAL_URL_FILE}" ]]; then
  APP_URL="$(tr -d '\r\n' < "${LOCAL_URL_FILE}")"
else
  APP_URL="http://127.0.0.1:8130"
fi

open "${APP_URL}" >/dev/null 2>&1 || true
echo "Hermes Stock Sentinel v1.0.0 is running at ${APP_URL}"
