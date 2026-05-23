from __future__ import annotations

import json
import math
import os
import errno
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from monitor_runtime import (
    append_analysis_snapshot,
    append_monitor_run,
    append_outbox,
    load_monitor_config,
    runtime_dir,
    runtime_path,
    utc_now_iso,
)

MONITOR_JOBS_FILE = "hermes_stock_monitors.json"
REALTIME_MONITOR_STATE_FILE = "hermes_realtime_monitor.json"
REALTIME_MONITOR_LOG_FILE = "hermes_realtime_monitor.log"
SNAPSHOT_DIR_NAME = "stock_snapshots"
LATEST_DIR_NAME = "stock_latest"

DEFAULT_INTERVAL_MINUTES = 30
DEFAULT_THRESHOLDS: dict[str, float] = {
    "interval_move_pct": 3.0,
    "day_change_pct": 5.0,
    "volume_ratio_high": 3.0,
    "volume_ratio_low": 0.30,
    "opening_gap_pct": 2.0,
    "protection_score_low": 35.0,
    "technical_score_low": 35.0,
}

ACTION_LABELS = {
    "continue_hold": "继续持有",
    "watch": "观察",
    "small_trial": "小仓试错",
    "reduce": "减仓",
    "sell": "卖出",
}

CAPABILITY_ANSWER_TEMPLATE = """我是 Hermes Stock Sentinel，本地 A 股监控和风控分析助手。

我可以做这些事：
1. 监控股票：你告诉我代码，例如 688766.SH，我会加入关注池并按间隔采集行情和 K 线。
2. 实时查询：我可以查询最新快照、涨跌幅、量比、保护分、技术分、支撑/压力位和历史摘要。
3. 趋势分析：我会结合 Hermes 风控、K 线、RSI、MACD、Bollinger、均线和本地历史判断偏强、震荡或偏弱。
4. 买卖辅助：我可以给出观察、小仓试错、继续持有、减仓或卖出的风控建议，并列出止损/复核条件。
5. 异动提醒：触发大涨跌、放量/缩量、跳空、保护分过低或技术面走弱时，会写入 outbox 等待推送。
6. 本地复盘：每次采集都会保存在本地 JSON/JSONL，后续分析会复用历史数据。

我的边界：
- 我不保证未来走势准确，也不会编造新闻、财报或内幕消息。
- 如果实时行情源不可用，我会明确标记数据错误，并降低分析置信度。
- 输出是风控和研究辅助，不是投资建议。

你可以这样问我：
- 监控 688766.SH，每 30 分钟看一次。
- 查询 688766.SH 现在怎么样。
- 分析 688766.SH 未来趋势和是否适合买入。
- 现在有哪些股票在实时监控。
- 停止实时监控。
"""


class StockAnalysisError(RuntimeError):
    """Raised when stock monitoring or analysis cannot be completed."""


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return deepcopy(default)


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _append_jsonl(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def _read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
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
    return rows[-limit:] if limit is not None else rows


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None or math.isnan(value) or math.isinf(value):
        return None
    return round(value, digits)


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def _max_drawdown_pct(values: list[float]) -> float | None:
    if not values:
        return None
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            max_drawdown = min(max_drawdown, (value - peak) / peak * 100)
    return round(max_drawdown, 2)


def normalize_thresholds(thresholds: dict[str, float] | None = None, merge_defaults: bool = True) -> dict[str, float]:
    threshold_map: dict[str, float] = deepcopy(DEFAULT_THRESHOLDS) if merge_defaults else {}
    for key, value in (thresholds or {}).items():
        if key not in DEFAULT_THRESHOLDS:
            raise StockAnalysisError(f"unknown threshold: {key}")
        threshold_map[key] = float(value)
    return threshold_map


def safe_symbol_for_file(symbol: str) -> str:
    normalized = str(symbol).strip().upper().replace("/", "_").replace(".", "_")
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in normalized)


def snapshot_dir() -> Path:
    path = runtime_dir() / SNAPSHOT_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def latest_dir() -> Path:
    path = runtime_dir() / LATEST_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def snapshot_path(symbol: str) -> Path:
    return snapshot_dir() / f"{safe_symbol_for_file(symbol)}.jsonl"


def latest_snapshot_path(symbol: str) -> Path:
    return latest_dir() / f"{safe_symbol_for_file(symbol)}.json"


def realtime_monitor_state_path() -> Path:
    return runtime_path(REALTIME_MONITOR_STATE_FILE)


def realtime_monitor_log_path() -> Path:
    return runtime_path(REALTIME_MONITOR_LOG_FILE)


def normalize_symbol(symbol: str) -> str:
    import server

    return server._normalize_watch_symbol(symbol)


def load_monitor_jobs(enabled_only: bool = False) -> list[dict[str, Any]]:
    data = _read_json(runtime_path(MONITOR_JOBS_FILE), [])
    jobs = data if isinstance(data, list) else []
    if enabled_only:
        return [job for job in jobs if job.get("enabled", True)]
    return jobs


def save_monitor_jobs(jobs: list[dict[str, Any]]) -> Path:
    jobs.sort(key=lambda item: str(item.get("symbol", "")))
    return _write_json(runtime_path(MONITOR_JOBS_FILE), jobs)


def register_stock_monitor(
    symbol: str,
    interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
    hermes_mode: str = "normal",
    note: str | None = None,
    target: str | None = None,
    thresholds: dict[str, float] | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    import server

    normalized = normalize_symbol(symbol)
    now = utc_now_iso()
    interval = max(1, int(interval_minutes))
    threshold_map = normalize_thresholds(thresholds)

    server._upsert_watchlist_item(symbol=normalized, note=note or "hermes-stock-monitor")

    jobs = load_monitor_jobs()
    for job in jobs:
        if job.get("symbol") == normalized:
            job.update(
                {
                    "interval_minutes": interval,
                    "hermes_mode": hermes_mode,
                    "note": note or job.get("note") or "hermes-stock-monitor",
                    "target": target if target is not None else job.get("target"),
                    "thresholds": threshold_map,
                    "enabled": enabled,
                    "updated_at": now,
                }
            )
            save_monitor_jobs(jobs)
            return job

    created = {
        "symbol": normalized,
        "interval_minutes": interval,
        "hermes_mode": hermes_mode,
        "note": note or "hermes-stock-monitor",
        "target": target,
        "thresholds": threshold_map,
        "enabled": enabled,
        "created_at": now,
        "updated_at": now,
        "last_collected_at": None,
        "last_alert_at": None,
    }
    jobs.append(created)
    save_monitor_jobs(jobs)
    return created


def update_monitor_job(symbol: str, updates: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    jobs = load_monitor_jobs()
    for job in jobs:
        if job.get("symbol") == normalized:
            job.update({key: value for key, value in updates.items() if value is not None})
            job["updated_at"] = utc_now_iso()
            save_monitor_jobs(jobs)
            return job
    raise StockAnalysisError(f"monitor job not found: {normalized}")


def monitor_job_due(job: dict[str, Any], now: datetime | None = None) -> bool:
    if not job.get("enabled", True):
        return False
    last_collected_at = _parse_dt(job.get("last_collected_at"))
    if last_collected_at is None:
        return True
    current = now or datetime.now(timezone.utc)
    interval = max(1, int(job.get("interval_minutes") or DEFAULT_INTERVAL_MINUTES))
    return current >= last_collected_at + timedelta(minutes=interval)


def load_stock_history(symbol: str, limit: int = 240) -> list[dict[str, Any]]:
    normalized = normalize_symbol(symbol)
    return _read_jsonl(snapshot_path(normalized), limit=limit)


def load_latest_snapshot(symbol: str) -> dict[str, Any] | None:
    normalized = normalize_symbol(symbol)
    data = _read_json(latest_snapshot_path(normalized), None)
    return data if isinstance(data, dict) else None


def load_realtime_monitor_state() -> dict[str, Any]:
    state = _read_json(realtime_monitor_state_path(), {})
    return state if isinstance(state, dict) else {}


def save_realtime_monitor_state(state: dict[str, Any]) -> Path:
    return _write_json(realtime_monitor_state_path(), state)


def process_running(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError as exc:
        if exc.errno == errno.EPERM:
            return True
        return False
    return True


def get_realtime_monitor_status() -> dict[str, Any]:
    state = load_realtime_monitor_state()
    pid = int(state.get("pid") or 0)
    running = process_running(pid)
    return {
        **state,
        "running": running,
        "pid": pid or None,
        "state_path": str(realtime_monitor_state_path()),
        "log_path": str(realtime_monitor_log_path()),
        "jobs": load_monitor_jobs(enabled_only=True),
    }


def compare_snapshots(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    threshold_map = normalize_thresholds(thresholds)
    quote = current.get("quote") or {}
    previous_quote = (previous or {}).get("quote") or {}
    kline = current.get("kline") or {}
    previous_kline = (previous or {}).get("kline") or {}

    current_price = _to_float(quote.get("last_price"))
    previous_price = _to_float(previous_quote.get("last_price"))
    interval_change_pct = _pct_change(current_price, previous_price) if previous else None
    day_change_pct = _to_float(quote.get("change_pct"))
    current_open = _to_float(quote.get("open"))
    previous_close = _to_float(quote.get("prev_close"))
    opening_gap_pct = _pct_change(current_open, previous_close) if current_open and previous_close else None
    volume_ratio = _to_float(quote.get("volume_ratio"))
    protection_score = _to_float(quote.get("protection_score"), 50)
    previous_protection_score = _to_float(previous_quote.get("protection_score"), 50)
    technical_score = _to_float(kline.get("technical_score"), 50)
    previous_technical_score = _to_float(previous_kline.get("technical_score"), 50)

    triggers: list[str] = []
    if interval_change_pct is not None and abs(interval_change_pct) >= threshold_map["interval_move_pct"]:
        triggers.append("interval_price_move")
    if abs(day_change_pct) >= threshold_map["day_change_pct"]:
        triggers.append("day_change_move")
    if volume_ratio >= threshold_map["volume_ratio_high"]:
        triggers.append("volume_ratio_high")
    if 0 < volume_ratio <= threshold_map["volume_ratio_low"]:
        triggers.append("volume_ratio_low")
    if opening_gap_pct is not None and abs(opening_gap_pct) >= threshold_map["opening_gap_pct"]:
        triggers.append("opening_gap")
    if protection_score <= threshold_map["protection_score_low"]:
        triggers.append("protection_score_low")
    if technical_score <= threshold_map["technical_score_low"]:
        triggers.append("technical_score_low")

    return {
        "previous_recorded_at": (previous or {}).get("recorded_at"),
        "current_price": current_price,
        "previous_price": previous_price if previous else None,
        "interval_change_pct": interval_change_pct,
        "day_change_pct": round(day_change_pct, 2),
        "opening_gap_pct": opening_gap_pct,
        "volume_ratio": round(volume_ratio, 2),
        "protection_score": round(protection_score, 2),
        "protection_score_delta": round(protection_score - previous_protection_score, 2) if previous else None,
        "technical_score": round(technical_score, 2),
        "technical_score_delta": round(technical_score - previous_technical_score, 2) if previous else None,
        "triggers": triggers,
        "alert_required": bool(triggers),
        "thresholds": threshold_map,
    }


def collect_stock_snapshot(
    symbol: str,
    hermes_mode: str = "normal",
    thresholds: dict[str, float] | None = None,
    source: str = "hermes-stock-monitor",
) -> dict[str, Any]:
    import server

    normalized = normalize_symbol(symbol)
    previous = load_latest_snapshot(normalized)
    analysis = server._build_symbol_analysis(normalized, hermes_mode=hermes_mode)
    snapshot = {
        "recorded_at": utc_now_iso(),
        "source": source,
        "symbol": normalized,
        "hermes_mode": hermes_mode,
        "quote": analysis.get("quote"),
        "kline": analysis.get("kline"),
        "kline_error": analysis.get("kline_error"),
        "quote_error": analysis.get("quote_error"),
        "position": analysis.get("position"),
        "decision": analysis.get("decision"),
    }
    snapshot["comparison"] = compare_snapshots(snapshot, previous, thresholds=thresholds)
    _append_jsonl(snapshot_path(normalized), snapshot)
    _write_json(latest_snapshot_path(normalized), snapshot)
    append_analysis_snapshot(
        {
            "recorded_at": snapshot["recorded_at"],
            "source": source,
            "symbol": normalized,
            "quote": snapshot["quote"],
            "comparison": snapshot["comparison"],
            "decision": snapshot["decision"],
        }
    )
    return snapshot


def build_alert_message(snapshot: dict[str, Any]) -> str:
    quote = snapshot.get("quote") or {}
    comparison = snapshot.get("comparison") or {}
    name = quote.get("name") or snapshot.get("symbol")
    triggers = ", ".join(comparison.get("triggers") or [])
    return "\n".join(
        [
            "【Hermes 股票监控提醒】",
            f"股票：{snapshot.get('symbol')} {name}",
            f"时间：{snapshot.get('recorded_at')}",
            f"现价：{quote.get('last_price')}，日涨跌：{comparison.get('day_change_pct')}%",
            f"区间涨跌：{comparison.get('interval_change_pct')}%，量比：{comparison.get('volume_ratio')}",
            f"保护分：{comparison.get('protection_score')}，技术分：{comparison.get('technical_score')}",
            f"触发项：{triggers or '无'}",
            "请复核仓位、止损位、支撑位和消息面变化。",
        ]
    )


def queue_snapshot_alert(snapshot: dict[str, Any], target: str | None = None) -> list[dict[str, Any]]:
    comparison = snapshot.get("comparison") or {}
    if not comparison.get("alert_required"):
        return []
    resolved_target = target or load_monitor_config().get("target")
    if not resolved_target:
        return []
    message = build_alert_message(snapshot)
    record = {
        "event_id": f"{snapshot.get('symbol')}|hermes-monitor|{snapshot.get('recorded_at')}",
        "created_at": snapshot.get("recorded_at"),
        "target": resolved_target,
        "channel": "hermes",
        "level": "high",
        "title": "Hermes 股票监控提醒",
        "body": message,
        "message": message,
        "payload": snapshot,
        "status": "pending",
        "attempt_count": 0,
        "sent_at": None,
        "last_error": None,
        "source": "hermes-stock-monitor",
    }
    append_outbox([record])
    return [record]


def run_registered_monitors(
    symbols: list[str] | None = None,
    only_due: bool = True,
    hermes_mode: str | None = None,
    queue_alerts: bool = True,
) -> dict[str, Any]:
    requested_symbols = {normalize_symbol(symbol) for symbol in symbols or []}
    jobs = load_monitor_jobs(enabled_only=True)
    if requested_symbols:
        jobs_by_symbol = {job.get("symbol"): job for job in jobs}
        for symbol in requested_symbols:
            if symbol not in jobs_by_symbol:
                jobs.append(register_stock_monitor(symbol))
    now = datetime.now(timezone.utc)
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for job in jobs:
        if requested_symbols and job.get("symbol") not in requested_symbols:
            continue
        if only_due and not monitor_job_due(job, now=now):
            skipped.append({"symbol": job.get("symbol"), "reason": "interval_not_due", "last_collected_at": job.get("last_collected_at")})
            continue
        selected.append(job)

    results: list[dict[str, Any]] = []
    queued_records: list[dict[str, Any]] = []
    updated_jobs = load_monitor_jobs()
    for job in selected:
        mode = hermes_mode or str(job.get("hermes_mode") or "normal")
        snapshot = collect_stock_snapshot(
            str(job["symbol"]),
            hermes_mode=mode,
            thresholds=job.get("thresholds") or DEFAULT_THRESHOLDS,
        )
        if queue_alerts:
            queued_records.extend(queue_snapshot_alert(snapshot, target=job.get("target")))
        results.append(snapshot)
        for existing in updated_jobs:
            if existing.get("symbol") == job.get("symbol"):
                existing["last_collected_at"] = snapshot["recorded_at"]
                if (snapshot.get("comparison") or {}).get("alert_required"):
                    existing["last_alert_at"] = snapshot["recorded_at"]
                existing["updated_at"] = snapshot["recorded_at"]
                break
    save_monitor_jobs(updated_jobs)

    payload = {
        "recorded_at": utc_now_iso(),
        "source": "hermes-stock-monitor",
        "only_due": only_due,
        "selected_symbols": [item.get("symbol") for item in selected],
        "skipped": skipped,
        "results": results,
        "queued_alert_records": queued_records,
    }
    if results:
        append_monitor_run(
            {
                "recorded_at": payload["recorded_at"],
                "source": payload["source"],
                "symbols": payload["selected_symbols"],
                "snapshot_count": len(results),
                "queued_alert_count": len(queued_records),
            }
        )
    return payload


def _ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    ema_values = [values[0]]
    for value in values[1:]:
        ema_values.append(value * alpha + ema_values[-1] * (1 - alpha))
    return ema_values


def _rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for prev, current in zip(values[-period - 1 : -1], values[-period:]):
        delta = current - prev
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = mean(gains)
    avg_loss = mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _slope_pct(values: list[float], window: int = 5) -> float | None:
    if len(values) <= window or values[-window - 1] == 0:
        return None
    return _pct_change(values[-1], values[-window - 1])


def calculate_indicators(bars: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [_to_float(row.get("close")) for row in bars if _to_float(row.get("close")) > 0]
    volumes = [_to_float(row.get("volume")) for row in bars]
    if not closes:
        return {
            "rsi14": None,
            "macd": None,
            "bollinger": None,
            "ma_alignment": "无数据",
            "ma20_slope_pct": None,
            "volume_trend": "无数据",
        }

    ema12 = _ema_series(closes, 12)
    ema26 = _ema_series(closes, 26)
    macd_line = [left - right for left, right in zip(ema12[-len(ema26) :], ema26)]
    signal_line = _ema_series(macd_line, 9) if macd_line else []
    histogram = macd_line[-1] - signal_line[-1] if macd_line and signal_line else None

    ma5 = mean(closes[-5:]) if len(closes) >= 5 else None
    ma20 = mean(closes[-20:]) if len(closes) >= 20 else None
    ma60 = mean(closes[-60:]) if len(closes) >= 60 else None
    if ma5 and ma20 and ma60 and ma5 > ma20 > ma60:
        ma_alignment = "多头排列"
    elif ma5 and ma20 and ma60 and ma5 < ma20 < ma60:
        ma_alignment = "空头排列"
    else:
        ma_alignment = "均线纠缠"

    bollinger = None
    if len(closes) >= 20:
        window = closes[-20:]
        mid = mean(window)
        deviation = pstdev(window)
        bollinger = {
            "middle": round(mid, 2),
            "upper": round(mid + 2 * deviation, 2),
            "lower": round(mid - 2 * deviation, 2),
            "width_pct": round((4 * deviation / mid) * 100, 2) if mid else None,
        }

    volume_trend = "量能平稳"
    if len(volumes) >= 20 and mean(volumes[-20:]) > 0:
        short_volume = mean(volumes[-5:]) if len(volumes) >= 5 else volumes[-1]
        long_volume = mean(volumes[-20:])
        ratio = short_volume / long_volume
        if ratio >= 1.35:
            volume_trend = "近5日放量"
        elif ratio <= 0.70:
            volume_trend = "近5日缩量"

    return {
        "rsi14": _rsi(closes, 14),
        "macd": {
            "dif": _round_or_none(macd_line[-1] if macd_line else None, 4),
            "dea": _round_or_none(signal_line[-1] if signal_line else None, 4),
            "histogram": _round_or_none(histogram, 4),
            "bias": "偏多" if histogram is not None and histogram > 0 else "偏空",
        },
        "bollinger": bollinger,
        "ma_alignment": ma_alignment,
        "ma20_slope_pct": _round_or_none(_slope_pct(closes[-20:], 5) if len(closes) >= 20 else None),
        "volume_trend": volume_trend,
    }


def summarize_history(history: list[dict[str, Any]]) -> dict[str, Any]:
    if not history:
        return {
            "sample_count": 0,
            "price_change_pct": None,
            "high": None,
            "low": None,
            "max_drawdown_pct": None,
            "avg_volume_ratio": None,
            "max_volume_ratio": None,
        }
    prices = [_to_float((item.get("quote") or {}).get("last_price")) for item in history]
    prices = [price for price in prices if price > 0]
    volume_ratios = [_to_float((item.get("quote") or {}).get("volume_ratio")) for item in history]
    volume_ratios = [ratio for ratio in volume_ratios if ratio > 0]
    high = max(prices) if prices else None
    low = min(prices) if prices else None
    return {
        "sample_count": len(history),
        "first_recorded_at": history[0].get("recorded_at"),
        "latest_recorded_at": history[-1].get("recorded_at"),
        "price_change_pct": _pct_change(prices[-1], prices[0]) if len(prices) >= 2 else None,
        "high": _round_or_none(high),
        "low": _round_or_none(low),
        "max_drawdown_pct": _max_drawdown_pct(prices),
        "avg_volume_ratio": _round_or_none(mean(volume_ratios), 2) if volume_ratios else None,
        "max_volume_ratio": _round_or_none(max(volume_ratios), 2) if volume_ratios else None,
    }


def _score_from_inputs(latest: dict[str, Any], indicators: dict[str, Any], history_summary: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    quote = latest.get("quote") or {}
    kline = latest.get("kline") or {}
    comparison = latest.get("comparison") or {}
    score = 50.0
    positives: list[str] = []
    risks: list[str] = []

    protection_score = _to_float(quote.get("protection_score"), 50)
    technical_score = _to_float(kline.get("technical_score"), 50)
    score += (protection_score - 50) * 0.35
    score += (technical_score - 50) * 0.30

    if quote.get("alert_level") == "high":
        score -= 18
        risks.append("Hermes 风险等级为 high")
    elif quote.get("alert_level") == "medium":
        score -= 8
        risks.append("Hermes 风险等级为 medium")

    if kline.get("trend_label") == "上升趋势":
        score += 8
        positives.append("K线处于上升趋势")
    elif kline.get("trend_label") == "下降趋势":
        score -= 10
        risks.append("K线处于下降趋势")

    ma_alignment = indicators.get("ma_alignment")
    if ma_alignment == "多头排列":
        score += 8
        positives.append("均线多头排列")
    elif ma_alignment == "空头排列":
        score -= 10
        risks.append("均线空头排列")

    macd = indicators.get("macd") or {}
    if macd.get("histogram") is not None and macd.get("histogram") > 0:
        score += 5
        positives.append("MACD 柱体为正")
    elif macd.get("histogram") is not None:
        score -= 5
        risks.append("MACD 柱体为负")

    rsi14 = indicators.get("rsi14")
    if rsi14 is not None:
        if 45 <= rsi14 <= 65:
            score += 4
            positives.append("RSI 处于相对健康区间")
        elif rsi14 > 78:
            score -= 8
            risks.append("RSI 过热，追高风险增加")
        elif rsi14 < 30:
            score -= 4
            risks.append("RSI 偏弱，尚未确认反转")

    if comparison.get("alert_required"):
        score -= 8
        risks.append("本次采集触发波动阈值")

    price_change_pct = history_summary.get("price_change_pct")
    if price_change_pct is not None:
        if price_change_pct >= 2:
            score += 4
            positives.append("监控历史内价格走强")
        elif price_change_pct <= -2:
            score -= 5
            risks.append("监控历史内价格走弱")

    if latest.get("quote_error"):
        score -= 12
        risks.append("实时行情存在错误")
    if latest.get("kline_error"):
        score -= 6
        risks.append("K线数据源存在错误")

    return max(0, min(100, round(score))), positives, risks


def _build_recommendation(
    latest: dict[str, Any],
    score: int,
    positives: list[str],
    risks: list[str],
) -> dict[str, Any]:
    quote = latest.get("quote") or {}
    kline = latest.get("kline") or {}
    position = latest.get("position") or {}
    decision = latest.get("decision") or {}
    last_price = _to_float(quote.get("last_price"))
    stop_loss = _to_float(position.get("stop_loss"))
    target_price = _to_float(position.get("target_price"))
    support_price = _to_float(kline.get("support_price"))
    resistance_price = _to_float(kline.get("resistance_price"))
    action = "watch"

    if decision.get("decision") == "卖出" or quote.get("alert_level") == "high" or score <= 35:
        action = "sell"
    elif decision.get("decision") == "减仓" or score <= 48:
        action = "reduce"
    elif score >= 70 and quote.get("alert_level") == "low":
        action = "continue_hold" if position else "small_trial"
    elif score >= 58 and quote.get("alert_level") != "high":
        action = "watch"

    if stop_loss <= 0 and support_price > 0:
        stop_loss = round(support_price * 0.98, 2)
    if target_price <= 0 and resistance_price > 0:
        target_price = round(resistance_price, 2)

    position_sizing = "暂不新增仓位"
    if action == "small_trial":
        position_sizing = "仅适合小仓试错，单票仓位建议不超过计划仓位的 20%-30%"
    elif action == "continue_hold":
        position_sizing = "已有仓位可继续持有，但不建议因单次信号直接加满"
    elif action == "reduce":
        position_sizing = "降低风险敞口，优先把仓位降到可承受回撤范围"
    elif action == "sell":
        position_sizing = "先保护本金和已实现收益，卖出或强制复核"

    review_conditions = [
        "实时行情刷新失败或 K 线数据缺失时先暂停决策",
        "跌破止损位或支撑位后重新评估",
        "放量但价格无法突破压力位时降低追涨权重",
    ]
    if last_price > 0 and resistance_price > 0:
        review_conditions.append(f"若有效突破压力位 {resistance_price}，再复核趋势延续")
    if stop_loss > 0:
        review_conditions.append(f"若跌破 {stop_loss}，优先执行止损或减仓纪律")

    reasons = positives[:3] + risks[:4]
    if not reasons:
        reasons = ["当前数据不足以形成强趋势结论"]

    return {
        "action": action,
        "label": ACTION_LABELS[action],
        "score": score,
        "rationale": reasons,
        "position_sizing": position_sizing,
        "stop_loss_reference": stop_loss or None,
        "target_price_reference": target_price or None,
        "support_price": support_price or None,
        "resistance_price": resistance_price or None,
        "review_conditions": review_conditions,
    }


def build_stock_analysis(
    symbol: str,
    lookback: int = 240,
    hermes_mode: str = "normal",
    refresh: bool = False,
) -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    if refresh or not load_latest_snapshot(normalized):
        collect_stock_snapshot(normalized, hermes_mode=hermes_mode)

    history = load_stock_history(normalized, limit=lookback)
    if not history:
        raise StockAnalysisError(f"no snapshot history for {normalized}")

    latest = history[-1]
    bars = list(((latest.get("kline") or {}).get("bars") or []))
    indicators = calculate_indicators(bars)
    history_summary = summarize_history(history)
    score, positives, risks = _score_from_inputs(latest, indicators, history_summary)
    recommendation = _build_recommendation(latest, score, positives, risks)

    confidence = "低"
    if len(bars) >= 60 and len(history) >= 3 and not latest.get("quote_error"):
        confidence = "高"
    elif len(bars) >= 30 and not latest.get("quote_error"):
        confidence = "中"

    expected_direction = "震荡"
    if score >= 68:
        expected_direction = "偏强"
    elif score <= 42:
        expected_direction = "偏弱"

    return {
        "symbol": normalized,
        "generated_at": utc_now_iso(),
        "lookback": lookback,
        "latest_snapshot": latest,
        "history_summary": history_summary,
        "indicators": indicators,
        "analysis": {
            "expected_direction": expected_direction,
            "confidence": confidence,
            "positives": positives,
            "risks": risks,
            "data_limits": [
                "分析只基于本地行情、K线和持仓数据，不包含未接入的新闻、财报和宏观事件。",
                "未来走势不能被保证；这里输出的是风控倾向和交易纪律建议。",
            ],
        },
        "recommendation": recommendation,
    }


def build_stock_query(symbol: str, lookback: int = 240, refresh: bool = False, hermes_mode: str = "normal") -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    latest = load_latest_snapshot(normalized)
    if refresh or latest is None:
        latest = collect_stock_snapshot(normalized, hermes_mode=hermes_mode)

    history = load_stock_history(normalized, limit=lookback)
    analysis = build_stock_analysis(normalized, lookback=lookback, hermes_mode=hermes_mode, refresh=False)
    quote = (latest or {}).get("quote") or {}
    kline = (latest or {}).get("kline") or {}
    comparison = (latest or {}).get("comparison") or {}
    recommendation = analysis.get("recommendation") or {}

    summary = {
        "symbol": normalized,
        "name": quote.get("name") or normalized,
        "last_price": quote.get("last_price"),
        "change_pct": quote.get("change_pct"),
        "volume_ratio": quote.get("volume_ratio"),
        "alert_level": quote.get("alert_level"),
        "signal_bias": quote.get("signal_bias"),
        "protection_score": quote.get("protection_score"),
        "technical_score": kline.get("technical_score"),
        "trend_label": kline.get("trend_label"),
        "support_price": kline.get("support_price"),
        "resistance_price": kline.get("resistance_price"),
        "interval_change_pct": comparison.get("interval_change_pct"),
        "alert_required": comparison.get("alert_required"),
        "recommendation": recommendation.get("label"),
        "recommendation_score": recommendation.get("score"),
        "confidence": (analysis.get("analysis") or {}).get("confidence"),
        "quote_error": latest.get("quote_error") if latest else None,
        "kline_error": latest.get("kline_error") if latest else None,
    }
    return {
        "symbol": normalized,
        "generated_at": utc_now_iso(),
        "summary": summary,
        "latest_snapshot": latest,
        "history_count": len(history),
        "history_summary": analysis.get("history_summary"),
        "indicators": analysis.get("indicators"),
        "analysis": analysis.get("analysis"),
        "recommendation": recommendation,
    }


def build_capability_answer_template() -> dict[str, Any]:
    return {
        "name": "Hermes Stock Sentinel",
        "generated_at": utc_now_iso(),
        "template": CAPABILITY_ANSWER_TEMPLATE,
        "capabilities": [
            "A股代码搜索和关注池管理",
            "按间隔采集实时行情和日 K 线",
            "本地 JSON/JSONL 历史沉淀",
            "Hermes 风控分、风险标签和告警等级",
            "RSI、MACD、Bollinger、均线、支撑/压力等技术分析",
            "观察、小仓试错、继续持有、减仓、卖出的风控建议",
            "outbox 告警队列和 Server 酱、PushPlus、企业微信机器人发送",
            "本地实时监控进程的启动、状态查询和停止",
        ],
        "example_questions": [
            "监控 688766.SH，每 30 分钟看一次。",
            "查询 688766.SH 现在怎么样。",
            "分析 688766.SH 未来趋势和是否适合买入。",
            "现在有哪些股票在实时监控。",
            "停止实时监控。",
        ],
        "limits": [
            "不能保证未来走势准确。",
            "不编造新闻、财报或内幕消息。",
            "实时行情源不可用时会明确标记错误并降低置信度。",
            "输出是风控和研究辅助，不是投资建议。",
        ],
    }
