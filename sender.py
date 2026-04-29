from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from monitor_runtime import load_outbox, load_monitor_config, mark_outbox_records

SEND_TIMEOUT = 20


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.headers.update({"User-Agent": "Hermes-Stock-Sentinel-Sender/1.0"})
    return session


def summarize_for_delivery(message: str, analysis_model: str | None = None) -> str:
    # Phase 1 keeps delivery deterministic and lightweight.
    # A future phase can call MiniMax-M2.7-highspeed here when configured.
    if analysis_model:
        return f"{message}\n模型：{analysis_model}"
    return message


def parse_target(target: str) -> tuple[str, str]:
    if ":" not in target:
        raise ValueError("target must use channel:secret format")
    channel, secret = target.split(":", 1)
    channel = channel.strip().lower()
    secret = secret.strip()
    if not channel or not secret:
        raise ValueError("target channel or secret is empty")
    return channel, secret


def _send_serverchan(secret: str, message: str, session: requests.Session) -> dict[str, Any]:
    response = session.post(
        f"https://sctapi.ftqq.com/{secret}.send",
        data={"title": "Hermes 股票告警", "desp": message},
        timeout=SEND_TIMEOUT,
    )
    response.raise_for_status()
    return response.json() if response.text else {"ok": True}


def _send_pushplus(secret: str, message: str, session: requests.Session) -> dict[str, Any]:
    response = session.post(
        "https://www.pushplus.plus/send",
        json={"token": secret, "title": "Hermes 股票告警", "content": message, "template": "markdown"},
        timeout=SEND_TIMEOUT,
    )
    response.raise_for_status()
    return response.json() if response.text else {"ok": True}


def _send_wecom_bot(secret: str, message: str, session: requests.Session) -> dict[str, Any]:
    response = session.post(
        f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={secret}",
        json={"msgtype": "text", "text": {"content": message}},
        timeout=SEND_TIMEOUT,
    )
    response.raise_for_status()
    return response.json() if response.text else {"ok": True}


def send_message(target: str, message: str, analysis_model: str | None = None, session: requests.Session | None = None) -> dict[str, Any]:
    channel, secret = parse_target(target)
    final_message = summarize_for_delivery(message, analysis_model=analysis_model)
    http = session or _http_session()
    if channel in {"serverchan", "ftqq", "wechat"}:
        return _send_serverchan(secret, final_message, http)
    if channel in {"pushplus", "weixin"}:
        return _send_pushplus(secret, final_message, http)
    if channel in {"wecom_bot", "qywx", "wecom"}:
        return _send_wecom_bot(secret, final_message, http)
    raise ValueError(f"unsupported target channel: {channel}")


def flush_outbox(limit: int | None = None, session: requests.Session | None = None) -> dict[str, Any]:
    config = load_monitor_config()
    analysis_model = config.get("analysis_model")
    records = load_outbox()
    http = session or _http_session()

    sent = 0
    failed = 0
    skipped = 0
    processed = 0

    for record in records:
        if record.get("status") != "pending":
            skipped += 1
            continue
        if limit is not None and processed >= limit:
            skipped += 1
            continue

        processed += 1
        record["attempt_count"] = int(record.get("attempt_count", 0)) + 1
        try:
            result = send_message(
                target=str(record["target"]),
                message=str(record["message"]),
                analysis_model=analysis_model,
                session=http,
            )
            record["status"] = "sent"
            record["sent_at"] = utc_now_iso()
            record["last_error"] = None
            record["delivery_result"] = result
            sent += 1
        except Exception as exc:  # noqa: BLE001
            record["status"] = "failed"
            record["last_error"] = str(exc)
            record["failed_at"] = utc_now_iso()
            failed += 1

    mark_outbox_records(records)
    return {
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
        "processed": processed,
        "outbox_size": len(records),
    }


def retry_failed(limit: int | None = None) -> dict[str, Any]:
    records = load_outbox()
    for record in records:
        if record.get("status") == "failed":
            record["status"] = "pending"
    mark_outbox_records(records)
    return flush_outbox(limit=limit)


def sender_env_help() -> dict[str, str]:
    return {
        "serverchan": "target 示例: serverchan:SCTxxxxxxxx",
        "pushplus": "target 示例: pushplus:你的token",
        "wecom_bot": "target 示例: wecom_bot:企业微信机器人key",
    }
