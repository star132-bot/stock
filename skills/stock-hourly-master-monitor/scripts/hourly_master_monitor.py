#!/usr/bin/env python3
"""Hourly master monitor helper for Hermes Stock Sentinel.

This script is intentionally stored inside the repository skill directory so a
fresh clone has the reusable monitoring procedure and the executable helper in
one place.

It reuses the project's existing backend/runtime modules instead of creating a
second monitoring system:
- server._upsert_watchlist_item / _build_symbol_analysis / _run_monitor_cycle
- monitor_runtime.append_monitor_run / append_analysis_snapshot / append_outbox
- .runtime/monitor_runs.jsonl and .runtime/analysis_history.jsonl

Extra per-symbol hourly snapshots are written to:
.runtime/hourly_stock_snapshots/<SYMBOL>.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SNAPSHOT_DIR_NAME = "hourly_stock_snapshots"
MASTER_RUNS_FILE = "hourly_master_runs.jsonl"
MASTER_ALERTS_FILE = "hourly_master_alerts.jsonl"

DEFAULT_THRESHOLDS: dict[str, float] = {
    "hourly_move_pct": 3.0,
    "day_change_pct": 5.0,
    "volume_ratio_high": 3.0,
    "volume_ratio_low": 0.30,
    "price_gap_pct": 2.0,
}


class SkillError(RuntimeError):
    """Raised when the skill helper cannot complete a monitoring run."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_symbol_for_file(symbol: str) -> str:
    """Return a portable filename stem while keeping the exchange readable."""
    safe = str(symbol).strip().upper().replace("/", "_").replace(".", "_")
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in safe)


def runtime_dir() -> Path:
    from monitor_runtime import runtime_dir as project_runtime_dir

    return project_runtime_dir()


def snapshot_dir(base_runtime_dir: Path | None = None) -> Path:
    directory = (base_runtime_dir or runtime_dir()) / SNAPSHOT_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def append_jsonl(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, default=json_default) + "\n")
    return path


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    if limit is not None:
        return rows[-limit:]
    return rows


def append_symbol_snapshot(base_runtime_dir: Path, symbol: str, snapshot: dict[str, Any]) -> Path:
    path = snapshot_dir(base_runtime_dir) / f"{safe_symbol_for_file(symbol)}.jsonl"
    return append_jsonl(path, snapshot)


def load_symbol_history(base_runtime_dir: Path, symbol: str, limit: int = 24) -> list[dict[str, Any]]:
    path = snapshot_dir(base_runtime_dir) / f"{safe_symbol_for_file(symbol)}.jsonl"
    return read_jsonl(path, limit=limit)


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def compare_with_previous(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compare the latest snapshot with the prior hourly snapshot.

    Returns a compact comparison object used both by Hermes prompts and by the
    huge-volatility alert gate.
    """
    threshold_map = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    quote = current.get("quote") or {}
    previous_quote = (previous or {}).get("quote") or {}
    current_price = to_float(quote.get("last_price"))
    previous_price = to_float(previous_quote.get("last_price"))
    hourly_change_pct = pct_change(current_price, previous_price) if previous else None
    day_change_pct = to_float(quote.get("change_pct"))
    volume_ratio = to_float(quote.get("volume_ratio"))
    current_open = to_float(quote.get("open"))
    previous_close = to_float(quote.get("prev_close"))
    gap_pct = pct_change(current_open, previous_close) if current_open and previous_close else None

    triggers: list[str] = []
    if hourly_change_pct is not None and abs(hourly_change_pct) >= threshold_map["hourly_move_pct"]:
        triggers.append("hourly_price_move")
    if abs(day_change_pct) >= threshold_map["day_change_pct"]:
        triggers.append("day_change_move")
    if volume_ratio >= threshold_map["volume_ratio_high"]:
        triggers.append("volume_ratio_high")
    if 0 < volume_ratio <= threshold_map["volume_ratio_low"]:
        triggers.append("volume_ratio_low")
    if gap_pct is not None and abs(gap_pct) >= threshold_map["price_gap_pct"]:
        triggers.append("opening_gap")

    return {
        "previous_recorded_at": (previous or {}).get("recorded_at"),
        "current_price": current_price,
        "previous_price": previous_price if previous else None,
        "hourly_change_pct": hourly_change_pct,
        "day_change_pct": round(day_change_pct, 2),
        "volume_ratio": round(volume_ratio, 2),
        "gap_pct": gap_pct,
        "triggers": triggers,
        "alert_required": bool(triggers),
        "thresholds": threshold_map,
    }


def normalize_symbols(raw_symbols: list[str]) -> list[str]:
    import server

    normalized: list[str] = []
    for raw in raw_symbols:
        symbol = raw.strip()
        if not symbol:
            continue
        normalized_symbol = server._normalize_watch_symbol(symbol)
        if normalized_symbol not in normalized:
            normalized.append(normalized_symbol)
    return normalized


def ensure_watchlist(symbols: list[str], note: str | None = None) -> list[dict[str, Any]]:
    import server

    items: list[dict[str, Any]] = []
    for symbol in symbols:
        items.append(server._upsert_watchlist_item(symbol=symbol, note=note))
    return items


def build_symbol_snapshot(symbol: str, hermes_mode: str = "normal") -> dict[str, Any]:
    import server

    analysis = server._build_symbol_analysis(symbol, hermes_mode=hermes_mode)
    quote = analysis.get("quote") or {}
    return {
        "recorded_at": utc_now_iso(),
        "symbol": symbol,
        "quote": quote,
        "kline": analysis.get("kline"),
        "kline_error": analysis.get("kline_error"),
        "quote_error": analysis.get("quote_error"),
        "position": analysis.get("position"),
        "decision": analysis.get("decision"),
    }


def compact_symbol_result(snapshot: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    quote = snapshot.get("quote") or {}
    decision = snapshot.get("decision") or {}
    return {
        "symbol": snapshot.get("symbol"),
        "name": quote.get("name") or snapshot.get("symbol"),
        "last_price": quote.get("last_price"),
        "day_change_pct": quote.get("change_pct"),
        "hourly_change_pct": comparison.get("hourly_change_pct"),
        "volume_ratio": quote.get("volume_ratio"),
        "alert_level": quote.get("alert_level"),
        "signal_bias": quote.get("signal_bias"),
        "risk_flags": quote.get("risk_flags"),
        "triggers": comparison.get("triggers"),
        "decision_action": decision.get("action") or decision.get("recommendation"),
        "decision_summary": decision.get("summary") or decision.get("reason"),
    }


def build_master_prompt(payload: dict[str, Any]) -> str:
    """Build the prompt Hermes/MiniMax should use for expert-style analysis."""
    compact_results = []
    for result in payload.get("results", []):
        if "quote" in result:
            compact_results.append(
                {
                    "symbol": result.get("symbol"),
                    "quote": result.get("quote"),
                    "comparison": result.get("comparison"),
                    "decision": result.get("decision"),
                }
            )
        else:
            compact_results.append(result)

    return f"""你是一个克制、风险优先的股票大师和A股投资研究员。请基于下面的真实行情快照、历史对比和项目内置风控结果，输出投资可行性分析。

要求：
1. 先判断是否存在巨大波动；如有，用【紧急提醒】开头。
2. 每只股票给出：趋势、量价、风险、历史对比、投资可行性、操作建议。
3. 明确区分“可观察 / 可小仓试错 / 暂不适合 / 需要减仓或止损”。
4. 给出仓位建议、止损位/复核条件，不要鼓励满仓或无脑追涨。
5. 如果数据不足，直接说明数据不足，不要编造财务或新闻。
6. 结尾加一句：这不是投资建议，只是基于当前数据的风控分析。

监控时间：{payload.get('recorded_at')}
是否触发巨大波动：{payload.get('alert_required')}
监控结果 JSON：
{json.dumps(compact_results, ensure_ascii=False, indent=2, default=json_default)}
""".strip()


def build_alert_message(payload: dict[str, Any]) -> str:
    alert_results = [item for item in payload.get("results", []) if (item.get("comparison") or {}).get("alert_required")]
    if not alert_results:
        return ""
    lines = ["【股票巨大波动提醒】"]
    lines.append(f"时间：{payload.get('recorded_at')}")
    for item in alert_results:
        quote = item.get("quote") or {}
        comparison = item.get("comparison") or {}
        name = quote.get("name") or item.get("symbol")
        lines.append(
            f"- {item.get('symbol')} {name}: 现价 {quote.get('last_price')}，"
            f"日涨跌 {comparison.get('day_change_pct')}%，"
            f"小时涨跌 {comparison.get('hourly_change_pct')}%，"
            f"量比 {comparison.get('volume_ratio')}，触发 {', '.join(comparison.get('triggers') or [])}"
        )
    lines.append("请复核仓位、止损线和是否有消息面变化。")
    return "\n".join(lines)


def queue_master_alert(payload: dict[str, Any], target: str | None = None) -> list[dict[str, Any]]:
    if not payload.get("alert_required"):
        return []
    from monitor_runtime import append_outbox

    record = {
        "id": f"hourly-master|{payload.get('recorded_at')}",
        "created_at": payload.get("recorded_at"),
        "target": target,
        "channel": "hermes",
        "level": "high",
        "title": "股票巨大波动提醒",
        "body": build_alert_message(payload),
        "payload": payload,
        "status": "pending",
        "source": "stock-hourly-master-monitor",
    }
    append_outbox([record])
    return [record]


def run_hourly_monitor(
    symbols: list[str] | None = None,
    hermes_mode: str = "normal",
    note: str | None = None,
    target: str | None = None,
    queue_alert: bool = True,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run one hourly cycle and persist all data needed for future comparison."""
    from monitor_runtime import append_analysis_snapshot, append_monitor_run, load_watchlist
    import server

    runtime = runtime_dir()
    if symbols:
        normalized_symbols = normalize_symbols(symbols)
        ensure_watchlist(normalized_symbols, note=note or "hourly-master-monitor")
    else:
        normalized_symbols = [
            str(item.get("symbol"))
            for item in load_watchlist()
            if item.get("enabled", True) and item.get("symbol")
        ]
        normalized_symbols = normalize_symbols(normalized_symbols)

    if not normalized_symbols:
        raise SkillError("关注池为空。请先传入 --symbol 688766.SH 或添加 watchlist。")

    base_monitor_result = server._run_monitor_cycle(hermes_mode=hermes_mode)
    results: list[dict[str, Any]] = []
    alert_required = False

    for symbol in normalized_symbols:
        history = load_symbol_history(runtime, symbol, limit=2)
        previous = history[-1] if history else None
        snapshot = build_symbol_snapshot(symbol, hermes_mode=hermes_mode)
        comparison = compare_with_previous(snapshot, previous, thresholds=thresholds)
        append_symbol_snapshot(runtime, symbol, snapshot)
        alert_required = alert_required or comparison["alert_required"]
        results.append({**snapshot, "comparison": comparison})

    payload = {
        "recorded_at": utc_now_iso(),
        "source": "stock-hourly-master-monitor",
        "hermes_mode": hermes_mode,
        "symbols": normalized_symbols,
        "alert_required": alert_required,
        "results": results,
        "compact_results": [compact_symbol_result(item, item["comparison"]) for item in results],
        "base_monitor_status": base_monitor_result.get("monitor_status"),
        "base_alert_count": len(base_monitor_result.get("alerts") or []),
        "master_prompt": None,
    }
    payload["master_prompt"] = build_master_prompt(payload)

    append_jsonl(runtime / MASTER_RUNS_FILE, payload)
    append_monitor_run(
        {
            "recorded_at": payload["recorded_at"],
            "source": payload["source"],
            "symbols": normalized_symbols,
            "alert_required": alert_required,
            "compact_results": payload["compact_results"],
        }
    )
    append_analysis_snapshot(
        {
            "recorded_at": payload["recorded_at"],
            "source": payload["source"],
            "alert_required": alert_required,
            "symbols": normalized_symbols,
            "compact_results": payload["compact_results"],
        }
    )

    queued_records: list[dict[str, Any]] = []
    if queue_alert:
        queued_records = queue_master_alert(payload, target=target)
        if queued_records:
            append_jsonl(runtime / MASTER_ALERTS_FILE, {"recorded_at": payload["recorded_at"], "records": queued_records})
    payload["queued_alert_records"] = queued_records
    return payload


def parse_threshold_overrides(values: list[str] | None) -> dict[str, float]:
    overrides: dict[str, float] = {}
    for item in values or []:
        if "=" not in item:
            raise SkillError(f"阈值格式错误: {item}，应为 key=value")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if key not in DEFAULT_THRESHOLDS:
            raise SkillError(f"未知阈值: {key}，可选: {', '.join(DEFAULT_THRESHOLDS)}")
        overrides[key] = float(raw_value)
    return overrides


def print_summary(payload: dict[str, Any]) -> None:
    print(json.dumps(
        {
            "ok": True,
            "recorded_at": payload.get("recorded_at"),
            "symbols": payload.get("symbols"),
            "alert_required": payload.get("alert_required"),
            "compact_results": payload.get("compact_results"),
            "queued_alert_count": len(payload.get("queued_alert_records") or []),
            "runtime_dir": str(runtime_dir()),
            "master_prompt": payload.get("master_prompt"),
        },
        ensure_ascii=False,
        indent=2,
        default=json_default,
    ))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one hourly Stock Sentinel monitoring cycle and persist per-symbol history.",
    )
    parser.add_argument("--symbol", action="append", dest="symbol", help="A股代码，可重复，如 --symbol 688766.SH --symbol 300750.SZ")
    parser.add_argument("--symbols", help="逗号分隔的A股代码，如 688766.SH,300750.SZ")
    parser.add_argument("--hermes-mode", default="normal", choices=["normal", "defensive", "crash"], help="复用项目风控模式")
    parser.add_argument("--note", default="hourly-master-monitor", help="写入 watchlist 的备注")
    parser.add_argument("--target", default=None, help="告警 outbox 目标，例如 weixin/feishu/telegram target")
    parser.add_argument("--no-queue-alert", action="store_true", help="巨大波动时不写入 outbox，只保存快照")
    parser.add_argument("--threshold", action="append", help="覆盖阈值，格式 key=value；key 可为 hourly_move_pct/day_change_pct/volume_ratio_high/volume_ratio_low/price_gap_pct")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    symbols: list[str] = []
    if args.symbols:
        symbols.extend([item.strip() for item in args.symbols.split(",") if item.strip()])
    if args.symbols is not None and args.symbol:
        symbols.extend(args.symbol)
    elif args.symbol:
        symbols.extend(args.symbol)

    payload = run_hourly_monitor(
        symbols=symbols or None,
        hermes_mode=args.hermes_mode,
        note=args.note,
        target=args.target,
        queue_alert=not args.no_queue_alert,
        thresholds=parse_threshold_overrides(args.threshold),
    )
    print_summary(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
