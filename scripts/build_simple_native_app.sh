#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

mkdir -p .runtime/bin
mkdir -p .runtime/swift-module-cache .runtime/clang-module-cache

export CLANG_MODULE_CACHE_PATH="${PROJECT_ROOT}/.runtime/clang-module-cache"
export SWIFT_MODULE_CACHE_PATH="${PROJECT_ROOT}/.runtime/swift-module-cache"

xcrun swiftc \
  -module-cache-path "${PROJECT_ROOT}/.runtime/swift-module-cache" \
  -framework AppKit \
  native/SimplifiedStockMonitorApp.swift \
  -o .runtime/bin/SimplifiedStockMonitor

echo "${PROJECT_ROOT}/.runtime/bin/SimplifiedStockMonitor"
