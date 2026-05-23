from pathlib import Path

from fastapi.testclient import TestClient

import server
from monitor_runtime import load_outbox
from stock_analysis_service import (
    StockAnalysisError,
    build_capability_answer_template,
    build_stock_analysis,
    build_stock_query,
    get_realtime_monitor_status,
    load_monitor_jobs,
    load_stock_history,
    register_stock_monitor,
    run_registered_monitors,
)


def sample_analysis(symbol: str = "688766.SH") -> dict:
    bars = []
    for index in range(70):
        close = 90 + index * 0.35
        bars.append(
            {
                "date": f"2026-04-{(index % 28) + 1:02d}",
                "open": close - 0.2,
                "close": close,
                "high": close + 0.5,
                "low": close - 0.7,
                "volume": 100000 + index * 1000,
            }
        )
    return {
        "quote": {
            "symbol": symbol,
            "name": "普冉股份",
            "market": "CN",
            "last_price": 114.15,
            "change_pct": 1.2,
            "change_abs": 1.35,
            "prev_close": 112.8,
            "open": 113.0,
            "high": 115.0,
            "low": 112.5,
            "volume": 190000,
            "turnover": 21000000,
            "bid": 114.1,
            "ask": 114.2,
            "spread_bps": 8.76,
            "volume_ratio": 1.4,
            "volatility_pct": 2.21,
            "provider": "tencent_quote",
            "ts_event": "2026-05-20T07:00:00+00:00",
            "protection_score": 72,
            "technical_score": 74,
            "alert_level": "low",
            "signal_bias": "偏强跟踪",
            "risk_flags": [],
            "summary": "暂未触发高优先级风险事件，继续观察。",
        },
        "kline": {
            "bars": bars,
            "latest_bar": bars[-1],
            "ma": {"ma5": 113.45, "ma10": 112.6, "ma20": 110.85, "ma60": 103.65},
            "volume_ma": {"ma5": 167000, "ma20": 159000},
            "trend_label": "上升趋势",
            "volume_price_summary": "上升趋势，最新K线为阳线，量能平稳，站上MA20。",
            "technical_score": 74,
            "technical_bias": "趋势保持",
            "support_price": 106.8,
            "resistance_price": 115.0,
        },
        "kline_error": None,
        "quote_error": None,
        "position": None,
        "decision": {"decision": "继续持有", "reasons": ["趋势和保护分保持强势"]},
    }


def test_register_monitor_collects_snapshot_and_builds_analysis(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setattr(server, "_build_symbol_analysis", lambda symbol, hermes_mode="normal": sample_analysis(symbol))

    job = register_stock_monitor("688766", interval_minutes=15, target="pushplus:test-token")
    assert job["symbol"] == "688766.SH"
    assert load_monitor_jobs()[0]["interval_minutes"] == 15

    result = run_registered_monitors(symbols=["688766.SH"], only_due=False)
    assert result["selected_symbols"] == ["688766.SH"]
    assert len(load_stock_history("688766.SH")) == 1

    analysis = build_stock_analysis("688766.SH")
    assert analysis["recommendation"]["label"] in {"小仓试错", "继续持有", "观察"}
    assert analysis["indicators"]["rsi14"] is not None
    assert analysis["history_summary"]["sample_count"] == 1


def test_run_registered_monitors_queues_alert_when_threshold_triggers(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    payload = sample_analysis()
    payload["quote"] = {**payload["quote"], "change_pct": -6.2, "alert_level": "high", "protection_score": 24}
    monkeypatch.setattr(server, "_build_symbol_analysis", lambda symbol, hermes_mode="normal": payload)

    register_stock_monitor("688766.SH", interval_minutes=30, target="pushplus:test-token")
    result = run_registered_monitors(symbols=["688766.SH"], only_due=False)

    assert result["results"][0]["comparison"]["alert_required"] is True
    assert result["queued_alert_records"]
    assert load_outbox()[0]["target"] == "pushplus:test-token"


def test_query_returns_latest_summary_and_analysis(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setattr(server, "_build_symbol_analysis", lambda symbol, hermes_mode="normal": sample_analysis(symbol))

    register_stock_monitor("688766.SH")
    run_registered_monitors(symbols=["688766.SH"], only_due=False)
    query = build_stock_query("688766.SH")

    assert query["summary"]["symbol"] == "688766.SH"
    assert query["summary"]["recommendation"] in {"小仓试错", "继续持有", "观察", "减仓", "卖出"}
    assert query["history_count"] == 1


def test_capability_template_describes_monitoring_features():
    payload = build_capability_answer_template()

    assert "Hermes Stock Sentinel" in payload["template"]
    assert "监控股票" in payload["template"]
    assert any("实时监控" in item for item in payload["capabilities"])


def test_realtime_monitor_status_reports_not_running_without_pid(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    status = get_realtime_monitor_status()

    assert status["running"] is False
    assert status["pid"] is None
    assert status["jobs"] == []


def test_hermes_stock_monitor_api_registers_queries_and_analyzes(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setattr(server, "_build_symbol_analysis", lambda symbol, hermes_mode="normal": sample_analysis(symbol))
    client = TestClient(server.app)

    create = client.post(
        "/api/hermes/stock-monitors",
        json={"symbol": "688766", "interval_minutes": 30, "run_now": True},
    )
    assert create.status_code == 200
    assert create.json()["item"]["symbol"] == "688766.SH"

    history = client.get("/api/hermes/stock-monitors/688766.SH/history")
    assert history.status_code == 200
    assert history.json()["count"] == 1

    query = client.get("/api/hermes/stock-monitors/688766.SH/query")
    assert query.status_code == 200
    assert query.json()["summary"]["symbol"] == "688766.SH"

    analysis = client.get("/api/hermes/stock-monitors/688766.SH/analysis")
    assert analysis.status_code == 200
    assert analysis.json()["symbol"] == "688766.SH"
    assert "recommendation" in analysis.json()

    status = client.get("/api/hermes/stock-monitors/realtime/status")
    assert status.status_code == 200
    assert status.json()["status"]["running"] is False

    capabilities = client.get("/api/hermes/capabilities")
    assert capabilities.status_code == 200
    assert "template" in capabilities.json()


def test_unknown_threshold_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))

    try:
        register_stock_monitor("688766.SH", thresholds={"typo_threshold": 1.0})
    except StockAnalysisError as exc:
        assert "unknown threshold" in str(exc)
    else:
        raise AssertionError("expected StockAnalysisError")
