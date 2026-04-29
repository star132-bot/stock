from pathlib import Path

from monitor_runtime import load_outbox, save_monitor_config, save_outbox
import sender


class DummyResponse:
    def __init__(self, payload=None):
        self._payload = payload or {"code": 0}
        self.text = "ok"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class DummySession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return DummyResponse()


def test_send_message_supports_pushplus(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    session = DummySession()
    result = sender.send_message("pushplus:test-token", "hello", session=session)
    assert result["code"] == 0
    assert "pushplus.plus/send" in session.calls[0][0]


def test_flush_outbox_marks_sent(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    save_monitor_config({"target": "pushplus:test-token", "analysis_model": "MiniMax-M2.7-highspeed"})
    save_outbox(
        [
            {
                "event_id": "688766.SH|high|drawdown_expanding|2026-04-26T06:00",
                "target": "pushplus:test-token",
                "message": "[HIGH] 688766.SH 回撤扩张",
                "created_at": "2026-04-26T06:00:00+00:00",
                "status": "pending",
                "sent_at": None,
                "last_error": None,
                "attempt_count": 0,
            }
        ]
    )
    session = DummySession()
    result = sender.flush_outbox(session=session)
    assert result["sent"] == 1
    outbox = load_outbox()
    assert outbox[0]["status"] == "sent"
    assert outbox[0]["sent_at"] is not None
    assert outbox[0]["attempt_count"] == 1


def test_flush_outbox_marks_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STOCK_RUNTIME_DIR", str(tmp_path / ".runtime"))
    save_monitor_config({"target": "unknown:test"})
    save_outbox(
        [
            {
                "event_id": "x",
                "target": "unknown:test",
                "message": "oops",
                "created_at": "2026-04-26T06:00:00+00:00",
                "status": "pending",
                "sent_at": None,
                "last_error": None,
                "attempt_count": 0,
            }
        ]
    )
    result = sender.flush_outbox()
    assert result["failed"] == 1
    outbox = load_outbox()
    assert outbox[0]["status"] == "failed"
    assert "unsupported target channel" in outbox[0]["last_error"]
