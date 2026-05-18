#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -n "${HERMES_PYTHON_BIN:-}" ]] && [[ -x "${HERMES_PYTHON_BIN}" ]]; then
  PYTHON_BIN="${HERMES_PYTHON_BIN}"
elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.11)"
elif command -v python3.10 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.10)"
else
  PYTHON_BIN="$(command -v python3)"
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  echo "简化股票监控需要 Python 3.10+。"
  echo "请安装 Python 3.11，或设置 HERMES_PYTHON_BIN=/path/to/python3.11"
  read -r -p "按回车退出..."
  exit 1
fi

"$PYTHON_BIN" simplified_stock_monitor.py

echo
read -r -p "简化股票监控已退出，按回车关闭窗口..."
