#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

bash "${PROJECT_ROOT}/scripts/start_v1_dashboard.sh"
