from __future__ import annotations

from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return round(sum(values[-window:]) / window, 2)


def _trend_label(close: float, ma20: float | None, ma60: float | None) -> str:
    if ma20 is None or ma60 is None:
        return "数据不足"
    if close > ma20 > ma60:
        return "上升趋势"
    if close < ma20 < ma60:
        return "下降趋势"
    return "震荡区间"


def analyze_kline_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "bars": [],
            "latest_bar": None,
            "ma": {},
            "volume_ma": {},
            "trend_label": "无数据",
            "volume_price_summary": "暂无K线数据。",
            "technical_score": 0,
            "technical_bias": "无法判断",
            "support_price": None,
            "resistance_price": None,
        }

    closes = [_to_float(row.get("close")) for row in rows]
    opens = [_to_float(row.get("open")) for row in rows]
    highs = [_to_float(row.get("high")) for row in rows]
    lows = [_to_float(row.get("low")) for row in rows]
    volumes = [_to_float(row.get("volume")) for row in rows]
    latest = rows[-1]
    latest_close = closes[-1]
    latest_open = opens[-1]
    latest_volume = volumes[-1]
    prev_close = closes[-2] if len(closes) >= 2 else latest_close

    ma5 = _ma(closes, 5)
    ma10 = _ma(closes, 10)
    ma20 = _ma(closes, 20)
    ma60 = _ma(closes, 60)
    vol_ma5 = _ma(volumes, 5)
    vol_ma20 = _ma(volumes, 20)
    support_price = round(min(lows[-20:]), 2) if len(lows) >= 20 else round(min(lows), 2)
    resistance_price = round(max(highs[-20:]), 2) if len(highs) >= 20 else round(max(highs), 2)
    trend_label = _trend_label(latest_close, ma20, ma60)

    volume_state = "量能平稳"
    if vol_ma20 and latest_volume > vol_ma20 * 1.4:
        volume_state = "放量"
    elif vol_ma20 and latest_volume < vol_ma20 * 0.7:
        volume_state = "缩量"

    candle_state = "阳线" if latest_close >= latest_open else "阴线"
    markers: list[str] = []
    if latest_close >= resistance_price * 0.995:
        markers.append("接近压力位")
    if latest_close <= support_price * 1.005:
        markers.append("接近支撑位")
    if ma20 and latest_close > ma20:
        markers.append("站上MA20")
    elif ma20 and latest_close < ma20:
        markers.append("跌破MA20")

    technical_score = 50
    if ma20 and latest_close > ma20:
        technical_score += 10
    if ma60 and latest_close > ma60:
        technical_score += 10
    if latest_close > prev_close:
        technical_score += 6
    if volume_state == "放量":
        technical_score += 8
    if latest_close <= support_price * 1.01:
        technical_score -= 12
    if ma20 and latest_close < ma20:
        technical_score -= 10
    technical_score = max(0, min(100, technical_score))

    if technical_score >= 72:
        technical_bias = "趋势保持"
    elif technical_score >= 56:
        technical_bias = "偏强观察"
    elif technical_score <= 34:
        technical_bias = "技术走弱"
    else:
        technical_bias = "震荡观察"

    summary = f"{trend_label}，最新K线为{candle_state}，{volume_state}"
    if markers:
        summary += "，" + " / ".join(markers)
    summary += "。"

    return {
        "bars": rows[-60:],
        "latest_bar": latest,
        "ma": {"ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60},
        "volume_ma": {"ma5": vol_ma5, "ma20": vol_ma20},
        "trend_label": trend_label,
        "volume_price_summary": summary,
        "technical_score": technical_score,
        "technical_bias": technical_bias,
        "support_price": support_price,
        "resistance_price": resistance_price,
    }


def analyze_position_logic(
    quote: dict[str, Any],
    kline_analysis: dict[str, Any],
    position: dict[str, Any] | None = None,
) -> dict[str, Any]:
    last_price = _to_float(quote.get("last_price"))
    change_pct = _to_float(quote.get("change_pct"))
    protection_score = _to_float(quote.get("protection_score"), 50)
    technical_score = _to_float(kline_analysis.get("technical_score"), 50)

    position = position or {}
    avg_cost = _to_float(position.get("avg_cost"))
    stop_loss = _to_float(position.get("stop_loss"))
    target_price = _to_float(position.get("target_price"))
    quantity = _to_float(position.get("quantity"))
    thesis = str(position.get("thesis") or "")
    horizon = str(position.get("horizon") or "")

    pnl_pct = None
    if avg_cost > 0 and last_price > 0:
        pnl_pct = round((last_price - avg_cost) / avg_cost * 100, 2)

    decision = "观察"
    reasons: list[str] = []
    if stop_loss > 0 and last_price <= stop_loss:
        decision = "卖出"
        reasons.append("跌破止损位")
    elif protection_score <= 35 or technical_score <= 35 or change_pct <= -3:
        decision = "卖出"
        reasons.append("风险分过低或技术面明显走坏")
    elif target_price > 0 and last_price >= target_price:
        decision = "减仓"
        reasons.append("达到目标价，适合兑现部分利润")
    elif technical_score < 50 or protection_score < 50:
        decision = "减仓"
        reasons.append("技术面和保护分转弱")
    elif technical_score >= 72 and protection_score >= 68:
        decision = "继续持有"
        reasons.append("趋势和保护分保持强势")
    else:
        reasons.append("等待更清晰的趋势确认")

    if pnl_pct is not None and pnl_pct < -8 and decision == "观察":
        decision = "减仓"
        reasons.append("浮亏扩大，需先控制回撤")

    return {
        "decision": decision,
        "reasons": reasons,
        "pnl_pct": pnl_pct,
        "avg_cost": avg_cost or None,
        "stop_loss": stop_loss or None,
        "target_price": target_price or None,
        "quantity": quantity or None,
        "thesis": thesis,
        "horizon": horizon,
    }
