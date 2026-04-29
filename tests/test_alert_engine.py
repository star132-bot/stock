from datetime import datetime, timezone

from alert_engine import analyze_quote, build_outbox_records, detect_alert_events


def sample_quote(**overrides):
    quote = {
        "symbol": "688766.SH",
        "name": "普冉股份",
        "market": "CN",
        "last_price": 92.5,
        "change_pct": -3.6,
        "change_abs": -3.46,
        "prev_close": 95.96,
        "open": 95.2,
        "high": 95.4,
        "low": 91.1,
        "volume": 180000,
        "turnover": 16650000,
        "bid": 92.3,
        "ask": 92.7,
        "spread_bps": 43.24,
        "volume_ratio": 2.3,
        "volatility_pct": 4.48,
        "provider": "tencent_quote",
        "ts_event": "2026-04-26T06:00:00+00:00",
    }
    quote.update(overrides)
    return quote


def test_analyze_quote_flags_high_risk_drawdown():
    analysis = analyze_quote(sample_quote())

    assert analysis["alert_level"] == "high"
    assert analysis["signal_bias"] == "崩坏警戒"
    assert "drawdown_expanding" in analysis["risk_flags"]
    assert "volatility_overheat" in analysis["risk_flags"]
    assert analysis["protection_score"] <= 35


def test_detect_alert_events_respects_cooldown_and_escalation():
    analysis = analyze_quote(sample_quote(change_pct=-1.4, volatility_pct=3.2, spread_bps=4.1, volume_ratio=1.9))
    now = datetime(2026, 4, 26, 6, 0, tzinfo=timezone.utc)

    first_events, first_state = detect_alert_events([analysis], {}, cooldown_minutes=15, now=now)
    assert len(first_events) == 1
    assert first_events[0]["level"] == "medium"

    second_events, second_state = detect_alert_events(
        [analysis],
        first_state,
        cooldown_minutes=15,
        now=datetime(2026, 4, 26, 6, 5, tzinfo=timezone.utc),
    )
    assert second_events == []

    escalated = analyze_quote(sample_quote(change_pct=-4.1, volatility_pct=4.9, spread_bps=4.8))
    third_events, _ = detect_alert_events(
        [escalated],
        second_state,
        cooldown_minutes=15,
        now=datetime(2026, 4, 26, 6, 7, tzinfo=timezone.utc),
    )
    assert len(third_events) == 1
    assert third_events[0]["level"] == "high"


def test_build_outbox_records_formats_pending_messages():
    events = [
        {
            "event_id": "688766.SH|high|drawdown_expanding|2026-04-26T06:00",
            "headline": "688766.SH 回撤扩张，进入崩坏警戒",
            "body": "跌幅 -3.60%，量比 2.30，点差 43.24 bps，Hermes 建议优先复核仓位与支撑位。",
            "level": "high",
            "created_at": "2026-04-26T06:00:00+00:00",
        }
    ]

    records = build_outbox_records(events, target="telegram")

    assert len(records) == 1
    assert records[0]["status"] == "pending"
    assert records[0]["attempt_count"] == 0
    assert "[HIGH]" in records[0]["message"]
    assert "市场态势：市场观察" in records[0]["message"]
