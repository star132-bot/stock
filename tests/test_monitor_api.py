from pathlib import Path

from fastapi.testclient import TestClient

import server
from monitor_runtime import load_alert_state, load_monitor_status, load_outbox, load_watchlist


class RuntimeHarness:
    def __init__(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
        self.client = TestClient(server.app)


def test_watchlist_upsert_and_soft_delete(tmp_path, monkeypatch):
    harness = RuntimeHarness(tmp_path, monkeypatch)

    create = harness.client.post("/api/watchlist", json={"symbol": "688766", "note": "半导体"})
    assert create.status_code == 200
    payload = create.json()
    assert payload["item"]["symbol"] == "688766.SH"
    assert load_watchlist()[0]["enabled"] is True

    delete = harness.client.delete("/api/watchlist/688766.SH")
    assert delete.status_code == 200
    assert delete.json()["item"]["enabled"] is False


def test_risk_summary_returns_backend_ranked_alerts(tmp_path, monkeypatch):
    harness = RuntimeHarness(tmp_path, monkeypatch)
    harness.client.post("/api/watchlist", json={"symbol": "688766.SH"})

    monkeypatch.setattr(
        server,
        "_fetch_quotes",
        lambda symbols: [
            {
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
        ],
    )

    response = harness.client.get("/api/risk-summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["top_risks"][0]["symbol"] == "688766.SH"
    assert payload["top_risks"][0]["alert_level"] == "high"
    assert payload["alerts"][0]["level"] == "high"
    assert payload["market_pulse"]["label"] in {"防守区间", "紧急崩坏"}


def test_monitor_run_once_persists_alert_state_and_outbox(tmp_path, monkeypatch):
    harness = RuntimeHarness(tmp_path, monkeypatch)
    harness.client.post("/api/watchlist", json={"symbol": "688766.SH"})
    harness.client.post(
        "/api/monitor/config",
        json={"target": "telegram", "cooldown_minutes": 15, "min_level": "medium"},
    )

    monkeypatch.setattr(
        server,
        "_fetch_quotes",
        lambda symbols: [
            {
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
        ],
    )

    response = harness.client.post("/api/monitor/run-once")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert len(payload["alerts"]) == 1
    assert len(payload["outbox_records"]) == 1
    assert payload["delivery"]["queued"] == 1

    alert_state = load_alert_state()
    assert "688766.SH|drawdown_expanding" in alert_state

    outbox = load_outbox()
    assert outbox[0]["target"] == "telegram"
    assert outbox[0]["status"] == "pending"

    status = load_monitor_status()
    assert status["last_alert_count"] == 1
    assert status["last_quote_count"] == 1
