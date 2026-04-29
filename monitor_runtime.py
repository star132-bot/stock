from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
RUNTIME_ENV_VAR = "HERMES_STOCK_RUNTIME_DIR"

WATCHLIST_FILE = "watchlist.json"
ALERT_STATE_FILE = "alert_state.json"
OUTBOX_FILE = "outbox.json"
MONITOR_CONFIG_FILE = "monitor_config.json"
MONITOR_STATUS_FILE = "monitor_status.json"
ANALYSIS_HISTORY_FILE = "analysis_history.jsonl"
MONITOR_RUNS_FILE = "monitor_runs.jsonl"
NIGHTLY_SUMMARY_DIR = "nightly_summaries"
POSITION_BOOK_FILE = "position_book.json"
KLINE_CACHE_DIR = "kline_cache"

DEFAULT_MONITOR_CONFIG: dict[str, Any] = {
    "target": None,
    "cooldown_minutes": 15,
    "min_level": "medium",
    "analysis_model": "MiniMax-M2.7-highspeed",
}

DEFAULT_MONITOR_STATUS: dict[str, Any] = {
    "last_run_at": None,
    "last_success_at": None,
    "last_failure_at": None,
    "last_error": None,
    "last_alert_count": 0,
    "last_quote_count": 0,
    "nightly_last_written_for": None,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def runtime_dir() -> Path:
    configured = os.getenv(RUNTIME_ENV_VAR)
    if configured:
        return Path(configured).expanduser().resolve()
    return BASE_DIR / ".runtime"


def ensure_runtime_dir() -> Path:
    directory = runtime_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def runtime_path(filename: str) -> Path:
    return ensure_runtime_dir() / filename


def _read_json(filename: str, default: Any) -> Any:
    path = runtime_path(filename)
    if not path.exists():
        return deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return deepcopy(default)


def _write_json(filename: str, payload: Any) -> Path:
    path = runtime_path(filename)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _append_jsonl(filename: str, payload: dict[str, Any]) -> Path:
    path = runtime_path(filename)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def _read_jsonl(filename: str) -> list[dict[str, Any]]:
    path = runtime_path(filename)
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def load_watchlist() -> list[dict[str, Any]]:
    data = _read_json(WATCHLIST_FILE, [])
    return data if isinstance(data, list) else []


def save_watchlist(items: list[dict[str, Any]]) -> Path:
    return _write_json(WATCHLIST_FILE, items)


def load_alert_state() -> dict[str, Any]:
    data = _read_json(ALERT_STATE_FILE, {})
    return data if isinstance(data, dict) else {}


def save_alert_state(state: dict[str, Any]) -> Path:
    return _write_json(ALERT_STATE_FILE, state)


def load_outbox() -> list[dict[str, Any]]:
    data = _read_json(OUTBOX_FILE, [])
    return data if isinstance(data, list) else []


def save_outbox(items: list[dict[str, Any]]) -> Path:
    return _write_json(OUTBOX_FILE, items)


def append_outbox(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing = load_outbox()
    existing.extend(items)
    save_outbox(existing)
    return existing


def mark_outbox_records(updated_items: list[dict[str, Any]]) -> Path:
    return save_outbox(updated_items)


def load_monitor_config() -> dict[str, Any]:
    data = _read_json(MONITOR_CONFIG_FILE, DEFAULT_MONITOR_CONFIG)
    if not isinstance(data, dict):
        return deepcopy(DEFAULT_MONITOR_CONFIG)
    merged = deepcopy(DEFAULT_MONITOR_CONFIG)
    merged.update(data)
    return merged


def save_monitor_config(config: dict[str, Any]) -> Path:
    merged = deepcopy(DEFAULT_MONITOR_CONFIG)
    merged.update(config)
    return _write_json(MONITOR_CONFIG_FILE, merged)


def load_monitor_status() -> dict[str, Any]:
    data = _read_json(MONITOR_STATUS_FILE, DEFAULT_MONITOR_STATUS)
    if not isinstance(data, dict):
        return deepcopy(DEFAULT_MONITOR_STATUS)
    merged = deepcopy(DEFAULT_MONITOR_STATUS)
    merged.update(data)
    return merged


def save_monitor_status(status: dict[str, Any]) -> Path:
    merged = deepcopy(DEFAULT_MONITOR_STATUS)
    merged.update(status)
    return _write_json(MONITOR_STATUS_FILE, merged)


def load_position_book() -> list[dict[str, Any]]:
    data = _read_json(POSITION_BOOK_FILE, [])
    return data if isinstance(data, list) else []


def save_position_book(items: list[dict[str, Any]]) -> Path:
    return _write_json(POSITION_BOOK_FILE, items)


def append_analysis_snapshot(payload: dict[str, Any]) -> Path:
    return _append_jsonl(ANALYSIS_HISTORY_FILE, payload)


def load_analysis_history() -> list[dict[str, Any]]:
    return _read_jsonl(ANALYSIS_HISTORY_FILE)


def append_monitor_run(payload: dict[str, Any]) -> Path:
    return _append_jsonl(MONITOR_RUNS_FILE, payload)


def load_monitor_runs() -> list[dict[str, Any]]:
    return _read_jsonl(MONITOR_RUNS_FILE)


def nightly_summary_dir() -> Path:
    path = BASE_DIR / "docs" / NIGHTLY_SUMMARY_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def nightly_summary_path(summary_date: str) -> Path:
    return nightly_summary_dir() / f"{summary_date}.md"


def kline_cache_dir() -> Path:
    path = runtime_dir() / KLINE_CACHE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_kline_snapshot(symbol: str, rows: list[dict[str, Any]]) -> Path:
    safe_symbol = symbol.replace("/", "_")
    path = kline_cache_dir() / f"{safe_symbol}.json"
    payload = {
        "symbol": symbol,
        "saved_at": utc_now_iso(),
        "bars": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_kline_snapshot(symbol: str) -> dict[str, Any] | None:
    safe_symbol = symbol.replace("/", "_")
    path = kline_cache_dir() / f"{safe_symbol}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
