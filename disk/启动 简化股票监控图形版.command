#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -z "${HERMES_CORE_PYTHON:-}" ]]; then
  if [[ -n "${HERMES_PYTHON_BIN:-}" ]] && [[ -x "${HERMES_PYTHON_BIN}" ]]; then
    export HERMES_CORE_PYTHON="${HERMES_PYTHON_BIN}"
  elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    export HERMES_CORE_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
  elif [[ -x "/Users/starfeld/.pyenv/versions/3.11.12/bin/python" ]]; then
    export HERMES_CORE_PYTHON="/Users/starfeld/.pyenv/versions/3.11.12/bin/python"
  elif command -v python3.11 >/dev/null 2>&1; then
    export HERMES_CORE_PYTHON="$(command -v python3.11)"
  elif command -v python3.10 >/dev/null 2>&1; then
    export HERMES_CORE_PYTHON="$(command -v python3.10)"
  fi
fi

LOG_FILE="${PROJECT_ROOT}/.runtime/simple-gui.log"
mkdir -p "${PROJECT_ROOT}/.runtime"

APP_BIN="${PROJECT_ROOT}/.runtime/bin/SimplifiedStockMonitor"
SOURCE_FILE="${PROJECT_ROOT}/native/SimplifiedStockMonitorApp.swift"

if [[ ! -x "$APP_BIN" ]] || [[ "$SOURCE_FILE" -nt "$APP_BIN" ]]; then
  echo "正在构建简化股票监控原生窗口..."
  bash "${PROJECT_ROOT}/scripts/build_simple_native_app.sh" >"$LOG_FILE" 2>&1
fi

echo "正在启动简化股票监控原生窗口..."
"$APP_BIN" >>"$LOG_FILE" 2>&1
