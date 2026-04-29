from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

LEVEL_ORDER = {"low": 0, "medium": 1, "high": 2}

FLAG_TITLES = {
    "drawdown_expanding": "回撤扩张",
    "liquidity_deterioration": "流动性恶化",
    "volume_expansion": "量能放大",
    "volatility_overheat": "波动过热",
}

FLAG_SUMMARIES = {
    "drawdown_expanding": "跌幅扩大，进入回撤复核区。",
    "liquidity_deterioration": "盘口点差走阔，执行滑点风险抬升。",
    "volume_expansion": "量比放大，异动强度上升。",
    "volatility_overheat": "日内振幅偏高，波动风险升温。",
}

SIGNAL_BIAS_BY_LEVEL = {
    "high": "崩坏警戒",
    "medium": "防守优先",
    "low": "继续观察",
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_spread_bps(quote: dict[str, Any]) -> float:
    last_price = _to_float(quote.get("last_price"))
    bid = _to_float(quote.get("bid"))
    ask = _to_float(quote.get("ask"))
    if last_price <= 0 or bid <= 0 or ask <= 0:
        return 0.0
    return round(((ask - bid) / last_price) * 10000, 2)


def derive_volatility_pct(quote: dict[str, Any]) -> float:
    high = _to_float(quote.get("high"))
    low = _to_float(quote.get("low"))
    prev_close = _to_float(quote.get("prev_close"))
    reference = prev_close or _to_float(quote.get("last_price"))
    if reference <= 0 or high <= 0 or low <= 0:
        return 0.0
    return round(((high - low) / reference) * 100, 2)


def normalize_quote(quote: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(quote)
    normalized["symbol"] = str(quote.get("symbol", "")).upper()
    normalized["name"] = quote.get("name") or normalized["symbol"]
    normalized["market"] = quote.get("market") or "CN"
    normalized["last_price"] = round(_to_float(quote.get("last_price")), 2)
    normalized["change_pct"] = round(_to_float(quote.get("change_pct")), 2)
    normalized["change_abs"] = round(_to_float(quote.get("change_abs")), 2)
    normalized["prev_close"] = round(_to_float(quote.get("prev_close")), 2)
    normalized["open"] = round(_to_float(quote.get("open")), 2)
    normalized["high"] = round(_to_float(quote.get("high"), normalized["last_price"]), 2)
    normalized["low"] = round(_to_float(quote.get("low"), normalized["last_price"]), 2)
    normalized["volume"] = int(_to_float(quote.get("volume"), 0))
    normalized["turnover"] = int(_to_float(quote.get("turnover"), 0))
    normalized["bid"] = round(_to_float(quote.get("bid"), normalized["last_price"]), 2)
    normalized["ask"] = round(_to_float(quote.get("ask"), normalized["last_price"]), 2)
    normalized["volume_ratio"] = round(_to_float(quote.get("volume_ratio"), 0), 2)
    normalized["spread_bps"] = round(_to_float(quote.get("spread_bps"), compute_spread_bps(quote)), 2)
    normalized["volatility_pct"] = round(_to_float(quote.get("volatility_pct"), derive_volatility_pct(quote)), 2)
    normalized["provider"] = quote.get("provider") or "unknown"
    normalized["ts_event"] = quote.get("ts_event")
    return normalized


def analyze_quote(quote: dict[str, Any], hermes_mode: str = "normal") -> dict[str, Any]:
    normalized = normalize_quote(quote)
    mode_bias = {"normal": 0, "defensive": 6, "crash": 12}.get(hermes_mode, 0)

    spread_bps = normalized["spread_bps"]
    change_pct = normalized["change_pct"]
    volume_ratio = normalized["volume_ratio"]
    volatility_pct = normalized["volatility_pct"]

    momentum_score = round(max(0, min(100, 50 + change_pct * 10 + (volume_ratio - 1) * 12)))
    liquidity_score = round(max(0, min(100, 100 - spread_bps * 12 + volume_ratio * 5)))
    volatility_score = round(max(0, min(100, 100 - abs(volatility_pct - 2.2) * 18 - mode_bias)))
    protection_score = round(
        max(
            0,
            min(
                100,
                58
                + change_pct * 12
                + (volume_ratio - 1) * 14
                - max(volatility_pct - 3.1, 0) * 14
                - max(spread_bps - 3, 0) * 8
                - mode_bias,
            ),
        )
    )

    risk_flags: list[str] = []
    if change_pct <= -2.0:
        risk_flags.append("drawdown_expanding")
    if spread_bps >= 4.0:
        risk_flags.append("liquidity_deterioration")
    if volume_ratio >= 1.8:
        risk_flags.append("volume_expansion")
    if volatility_pct >= 3.5:
        risk_flags.append("volatility_overheat")

    if protection_score <= 35 or change_pct <= -3.0 or volatility_pct >= 4.2:
        alert_level = "high"
    elif protection_score <= 55 or spread_bps >= 4.0 or volume_ratio >= 1.8 or change_pct <= -2.0:
        alert_level = "medium"
    else:
        alert_level = "low"

    signal_bias = SIGNAL_BIAS_BY_LEVEL[alert_level]
    if alert_level == "low" and protection_score >= 78:
        signal_bias = "趋势确认"
    elif alert_level == "low" and protection_score >= 62:
        signal_bias = "偏强跟踪"

    summary_parts: list[str] = []
    if "drawdown_expanding" in risk_flags:
        summary_parts.append(f"跌幅 {change_pct:.2f}%")
    if "volume_expansion" in risk_flags:
        summary_parts.append(f"量比 {volume_ratio:.2f}")
    if "liquidity_deterioration" in risk_flags:
        summary_parts.append(f"点差 {spread_bps:.2f} bps")
    if "volatility_overheat" in risk_flags:
        summary_parts.append(f"振幅 {volatility_pct:.2f}%")

    if summary_parts:
        summary = "，".join(summary_parts) + "，进入高优先级复核区。"
    else:
        summary = "暂未触发高优先级风险事件，继续观察。"

    normalized.update(
        {
            "analysis": {
                "momentum_score": momentum_score,
                "liquidity_score": liquidity_score,
                "volatility_score": volatility_score,
                "protection_score": protection_score,
                "signal_bias": signal_bias,
                "alert_level": alert_level,
                "risk_flags": risk_flags,
                "summary": summary,
            }
        }
    )
    normalized.update(normalized["analysis"])
    return normalized


def rank_analyses(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> tuple[float, float]:
        risk_score = (100 - item.get("protection_score", 100)) + max(0.0, -_to_float(item.get("change_pct")) * 8)
        return (risk_score, LEVEL_ORDER.get(item.get("alert_level", "low"), 0))

    return sorted(analyses, key=sort_key, reverse=True)


def market_pulse(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    if not analyses:
        return {
            "label": "暂无监控",
            "detail": "当前观察池为空，尚未形成后端风险结论。",
            "klass": "neutral",
        }

    negatives = sum(1 for item in analyses if _to_float(item.get("change_pct")) < 0)
    average_change = sum(_to_float(item.get("change_pct")) for item in analyses) / len(analyses)
    high_risk_count = sum(1 for item in analyses if item.get("alert_level") == "high")

    if len(analyses) >= 2 and (high_risk_count >= max(2, (len(analyses) + 1) // 2) or average_change <= -1.4):
        return {
            "label": "紧急崩坏",
            "detail": "观察池多数标的进入高压状态，优先保护利润与本金。",
            "klass": "negative",
        }
    if negatives >= max(1, (len(analyses) + 1) // 2) or average_change <= -0.5:
        return {
            "label": "防守区间",
            "detail": "下跌家数增多，优先关注回撤扩张和流动性恶化。",
            "klass": "neutral",
        }
    return {
        "label": "可控状态",
        "detail": "市场暂无系统性崩坏，但仍需盯住异动和放量拐点。",
        "klass": "positive",
    }


def _choose_primary_flag(analysis: dict[str, Any]) -> str | None:
    flags = analysis.get("risk_flags") or []
    for name in ["drawdown_expanding", "liquidity_deterioration", "volume_expansion", "volatility_overheat"]:
        if name in flags:
            return name
    return flags[0] if flags else None


def _level_gte(left: str, right: str) -> bool:
    return LEVEL_ORDER.get(left, 0) >= LEVEL_ORDER.get(right, 0)


def detect_alert_events(
    analyses: list[dict[str, Any]],
    previous_state: dict[str, Any],
    cooldown_minutes: int,
    min_level: str = "medium",
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    current_time = now or datetime.now(timezone.utc)
    updated_state = dict(previous_state or {})
    events: list[dict[str, Any]] = []
    threshold = max(0, int(cooldown_minutes))

    for analysis in analyses:
        level = str(analysis.get("alert_level", "low"))
        if not _level_gte(level, min_level):
            continue

        primary_flag = _choose_primary_flag(analysis)
        if not primary_flag:
            continue

        symbol = str(analysis.get("symbol", "")).upper()
        state_key = f"{symbol}|{primary_flag}"
        state_entry = dict(updated_state.get(state_key) or {})
        last_level = state_entry.get("last_level")
        last_triggered_at_raw = state_entry.get("last_triggered_at")
        last_triggered_at = None
        if last_triggered_at_raw:
            try:
                last_triggered_at = datetime.fromisoformat(last_triggered_at_raw)
            except ValueError:
                last_triggered_at = None

        escalated = last_level is not None and LEVEL_ORDER.get(level, 0) > LEVEL_ORDER.get(last_level, 0)
        is_new = not state_entry
        cooldown_active = False
        if last_triggered_at is not None:
            cooldown_active = current_time < last_triggered_at + timedelta(minutes=threshold)

        should_emit = is_new or escalated or not cooldown_active
        if should_emit:
            title = FLAG_TITLES.get(primary_flag, primary_flag)
            event_id = f"{symbol}|{level}|{primary_flag}|{current_time.strftime('%Y-%m-%dT%H:%M')}"
            body = (
                f"跌幅 {analysis.get('change_pct', 0):.2f}%，量比 {analysis.get('volume_ratio', 0):.2f}，"
                f"点差 {analysis.get('spread_bps', 0):.2f} bps，Hermes 建议优先复核仓位与支撑位。"
            )
            events.append(
                {
                    "event_id": event_id,
                    "symbol": symbol,
                    "level": level,
                    "headline": f"{symbol} {title}，进入{analysis.get('signal_bias', '风险观察')}",
                    "body": body,
                    "market_pulse": None,
                    "cooldown_key": state_key,
                    "risk_flag": primary_flag,
                    "created_at": current_time.isoformat(),
                    "summary": FLAG_SUMMARIES.get(primary_flag, analysis.get("summary", "")),
                }
            )
            state_entry["last_event_id"] = event_id
            state_entry["last_triggered_at"] = current_time.isoformat()

        state_entry.update(
            {
                "symbol": symbol,
                "risk_flag": primary_flag,
                "last_level": level,
                "first_seen_at": state_entry.get("first_seen_at") or current_time.isoformat(),
                "last_change_pct": analysis.get("change_pct"),
                "last_volume_ratio": analysis.get("volume_ratio"),
                "last_spread_bps": analysis.get("spread_bps"),
            }
        )
        updated_state[state_key] = state_entry

    return events, updated_state


def build_outbox_records(events: list[dict[str, Any]], target: str | None, market_pulse_label: str | None = None) -> list[dict[str, Any]]:
    if not target:
        return []
    records: list[dict[str, Any]] = []
    for event in events:
        pulse_label = market_pulse_label or event.get("market_pulse") or "市场观察"
        records.append(
            {
                "event_id": event["event_id"],
                "target": target,
                "message": (
                    f"[{str(event.get('level', 'low')).upper()}] {event.get('headline')}\n"
                    f"{event.get('body')}\n"
                    f"市场态势：{pulse_label}"
                ),
                "created_at": event.get("created_at") or datetime.now(timezone.utc).isoformat(),
                "status": "pending",
                "sent_at": None,
                "last_error": None,
                "attempt_count": 0,
            }
        )
    return records
