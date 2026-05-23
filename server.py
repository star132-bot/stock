from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from alert_engine import analyze_quote, build_outbox_records, detect_alert_events, market_pulse, rank_analyses
from monitor_runtime import (
    append_outbox,
    append_analysis_snapshot,
    append_monitor_run,
    load_alert_state,
    load_analysis_history,
    load_monitor_config,
    load_monitor_status,
    load_monitor_runs,
    load_kline_snapshot,
    load_position_book,
    load_watchlist,
    runtime_dir,
    save_kline_snapshot,
    save_alert_state,
    save_monitor_config,
    save_monitor_status,
    save_position_book,
    save_watchlist,
    utc_now_iso,
)
from technical_analysis import analyze_kline_rows, analyze_position_logic
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
    update_monitor_job,
)

BASE_DIR = Path(__file__).resolve().parent
CATALOG_CACHE = runtime_dir() / "a_stock_catalog.json"
CN_SYMBOL_RE = re.compile(r"^\d{6}\.(SH|SZ)$")

app = FastAPI(title="Hermes Stock Sentinel API")
app.mount("/assets", StaticFiles(directory=BASE_DIR), name="assets")


class WatchlistUpsertRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    note: str | None = None


class MonitorConfigRequest(BaseModel):
    target: str | None = None
    cooldown_minutes: int | None = Field(default=None, ge=0, le=1440)
    min_level: str | None = None
    analysis_model: str | None = None


class PositionUpsertRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    quantity: float | None = Field(default=None, ge=0)
    avg_cost: float | None = Field(default=None, ge=0)
    stop_loss: float | None = Field(default=None, ge=0)
    target_price: float | None = Field(default=None, ge=0)
    horizon: str | None = None
    thesis: str | None = None


class StockMonitorRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    interval_minutes: int = Field(default=30, ge=1, le=1440)
    hermes_mode: str = "normal"
    note: str | None = None
    target: str | None = None
    thresholds: dict[str, float] | None = None
    run_now: bool = True


class StockMonitorPatchRequest(BaseModel):
    enabled: bool | None = None
    interval_minutes: int | None = Field(default=None, ge=1, le=1440)
    hermes_mode: str | None = None
    note: str | None = None
    target: str | None = None
    thresholds: dict[str, float] | None = None


def _http_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 Hermes-Stock-Sentinel/1.0",
            "Referer": "https://qt.gtimg.cn/",
        }
    )
    return session


def _infer_cn_symbol(code: str) -> str:
    if code.startswith(("6", "9")):
        return f"{code}.SH"
    return f"{code}.SZ"


def _tencent_symbol(symbol: str) -> str:
    code = symbol.split(".")[0]
    if symbol.endswith(".SH") or code.startswith(("6", "9")):
        return f"sh{code}"
    return f"sz{code}"


def _load_catalog_cache() -> list[dict[str, Any]]:
    if not CATALOG_CACHE.exists():
        return []
    try:
        return json.loads(CATALOG_CACHE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_catalog_cache(entries: list[dict[str, Any]]) -> None:
    CATALOG_CACHE.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_CACHE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_catalog() -> list[dict[str, Any]]:
    import akshare as ak

    df = ak.stock_info_a_code_name()
    entries: list[dict[str, Any]] = []
    for row in df.to_dict("records"):
        code = str(row.get("code", "")).strip()
        name = str(row.get("name", "")).strip()
        if len(code) != 6 or not code.isdigit() or not name:
            continue
        entries.append(
            {
                "symbol": _infer_cn_symbol(code),
                "code": code,
                "name": name,
                "market": "CN",
            }
        )
    _save_catalog_cache(entries)
    return entries


def _catalog() -> list[dict[str, Any]]:
    cached = _load_catalog_cache()
    if cached:
        return cached
    return _fetch_catalog()


def _search_catalog(query: str, limit: int = 20) -> list[dict[str, Any]]:
    normalized = query.strip().upper()
    if not normalized:
        return []
    matches: list[tuple[int, dict[str, Any]]] = []
    for item in _catalog():
        symbol = str(item["symbol"]).upper()
        code = str(item["code"]).upper()
        name = str(item["name"]).upper()
        score = None
        if normalized == symbol or normalized == code:
            score = 0
        elif symbol.startswith(normalized) or code.startswith(normalized):
            score = 1
        elif normalized in name:
            score = 2
        if score is not None:
            matches.append((score, item))
    matches.sort(key=lambda pair: (pair[0], pair[1]["code"]))
    return [item for _, item in matches[:limit]]


def _parse_tencent_line(line: str) -> dict[str, Any] | None:
    if "=" not in line:
        return None
    left, right = line.split("=", 1)
    payload = right.strip().strip(";").strip('"')
    if not payload:
        return None
    fields = payload.split("~")
    if len(fields) < 36:
        return None

    code_with_prefix = left.split("_", 1)[-1]
    code = code_with_prefix[2:] if len(code_with_prefix) > 2 else code_with_prefix
    symbol = f"{code}.SH" if code_with_prefix.startswith("sh") else f"{code}.SZ"
    trade_blob = fields[35].split("/") if len(fields) > 35 and fields[35] else []
    volume = int(float(trade_blob[1])) if len(trade_blob) > 1 and trade_blob[1] else int(float(fields[6] or 0))
    turnover = int(float(trade_blob[2])) if len(trade_blob) > 2 and trade_blob[2] else 0
    last_price = float(fields[3] or 0)
    prev_close = float(fields[4] or 0)
    open_price = float(fields[5] or 0)
    high = float(fields[33] or 0) if len(fields) > 33 and fields[33] else last_price
    low = float(fields[34] or 0) if len(fields) > 34 and fields[34] else last_price
    change_abs = round(last_price - prev_close, 2)
    change_pct = round((change_abs / prev_close) * 100, 2) if prev_close else 0.0
    bid = float(fields[9] or 0) if len(fields) > 9 and fields[9] else last_price
    ask = float(fields[19] or 0) if len(fields) > 19 and fields[19] else last_price
    volume_ratio = float(fields[38] or 0) if len(fields) > 38 and fields[38] else 0.0
    spread_bps = round(((ask - bid) / last_price) * 10000, 2) if last_price and ask and bid else 0.0

    timestamp_raw = fields[30] if len(fields) > 30 else ""
    ts_event = None
    if len(timestamp_raw) == 14 and timestamp_raw.isdigit():
        ts_event = datetime.strptime(timestamp_raw, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).isoformat()

    return {
        "symbol": symbol,
        "code": code,
        "name": fields[1],
        "market": "CN",
        "last_price": last_price,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "open": open_price,
        "high": high,
        "low": low,
        "prev_close": prev_close,
        "volume": volume,
        "turnover": turnover,
        "bid": bid,
        "ask": ask,
        "spread_bps": spread_bps,
        "volume_ratio": volume_ratio,
        "ts_event": ts_event,
        "provider": "tencent_quote",
    }


def _fetch_quotes(symbols: list[str]) -> list[dict[str, Any]]:
    if not symbols:
        return []
    query = ",".join(_tencent_symbol(symbol) for symbol in symbols)
    response = _http_session().get(f"https://qt.gtimg.cn/q={query}", timeout=15)
    response.raise_for_status()
    text = response.content.decode("gbk", errors="ignore")
    quotes: list[dict[str, Any]] = []
    for line in text.splitlines():
        parsed = _parse_tencent_line(line.strip())
        if parsed:
            quotes.append(parsed)
    return quotes


def _normalize_watch_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized.isdigit() and len(normalized) == 6:
        normalized = _infer_cn_symbol(normalized)
    if not CN_SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Phase 1 仅支持 A 股代码，格式如 688766.SH 或 300750.SZ")
    return normalized


def _enabled_watchlist_items() -> list[dict[str, Any]]:
    return [item for item in load_watchlist() if item.get("enabled", True)]


def _live_watchlist_items() -> list[dict[str, Any]]:
    return [item for item in _enabled_watchlist_items() if CN_SYMBOL_RE.fullmatch(str(item.get("symbol", "")))]


def _load_positions_by_symbol() -> dict[str, dict[str, Any]]:
    return {item["symbol"]: item for item in load_position_book() if item.get("symbol")}


def _fetch_daily_kline(symbol: str, limit: int = 120) -> list[dict[str, Any]]:
    import akshare as ak

    code = symbol.split(".")[0]
    df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
    if df.empty:
        return []
    rows: list[dict[str, Any]] = []
    for row in df.tail(limit).to_dict("records"):
        rows.append(
            {
                "date": str(row.get("日期")),
                "open": float(row.get("开盘", 0) or 0),
                "close": float(row.get("收盘", 0) or 0),
                "high": float(row.get("最高", 0) or 0),
                "low": float(row.get("最低", 0) or 0),
                "volume": float(row.get("成交量", 0) or 0),
                "turnover": float(row.get("成交额", 0) or 0),
                "amplitude_pct": float(row.get("振幅", 0) or 0),
                "change_pct": float(row.get("涨跌幅", 0) or 0),
                "change_abs": float(row.get("涨跌额", 0) or 0),
                "turnover_rate": float(row.get("换手率", 0) or 0),
            }
        )
    save_kline_snapshot(symbol, rows)
    return rows


def _fetch_tencent_daily_kline(symbol: str, limit: int = 120) -> list[dict[str, Any]]:
    tencent_symbol = _tencent_symbol(symbol)
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    response = _http_session().get(
        url,
        params={"param": f"{tencent_symbol},day,,,{limit},qfq"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    symbol_payload = (payload.get("data") or {}).get(tencent_symbol) or {}
    raw_rows = symbol_payload.get("qfqday") or symbol_payload.get("day") or []

    rows: list[dict[str, Any]] = []
    for item in raw_rows[-limit:]:
        if not isinstance(item, list) or len(item) < 6:
            continue
        open_price = float(item[1] or 0)
        close_price = float(item[2] or 0)
        high_price = float(item[3] or 0)
        low_price = float(item[4] or 0)
        volume = float(item[5] or 0)
        prev_close = rows[-1]["close"] if rows else close_price
        change_abs = close_price - prev_close
        rows.append(
            {
                "date": str(item[0]),
                "open": open_price,
                "close": close_price,
                "high": high_price,
                "low": low_price,
                "volume": volume,
                "turnover": 0,
                "amplitude_pct": round((high_price - low_price) / prev_close * 100, 2) if prev_close else 0,
                "change_pct": round(change_abs / prev_close * 100, 2) if prev_close else 0,
                "change_abs": round(change_abs, 2),
                "turnover_rate": 0,
            }
        )

    if rows:
        save_kline_snapshot(symbol, rows)
    return rows


def _load_daily_kline(symbol: str, limit: int = 120) -> list[dict[str, Any]]:
    errors: list[str] = []
    try:
        rows = _fetch_daily_kline(symbol, limit=limit)
        if rows:
            return rows
    except Exception as exc:
        errors.append(f"akshare: {exc}")

    try:
        rows = _fetch_tencent_daily_kline(symbol, limit=limit)
        if rows:
            return rows
    except Exception as exc:
        errors.append(f"tencent: {exc}")

    cached = load_kline_snapshot(symbol)
    cached_rows = list(cached.get("bars") or []) if cached else []
    if cached_rows:
        return cached_rows[-limit:]

    detail = "；".join(errors) if errors else "无可用数据源"
    raise HTTPException(status_code=502, detail=f"K线获取失败: {detail}")


def _build_symbol_analysis(symbol: str, hermes_mode: str = "normal") -> dict[str, Any]:
    normalized = _normalize_watch_symbol(symbol)
    quote_error = None
    try:
        quotes = _fetch_quotes([normalized])
    except Exception as exc:
        quotes = []
        quote_error = f"实时行情获取失败: {exc}"
    if quotes:
        quote = analyze_quote(quotes[0], hermes_mode=hermes_mode)
    else:
        quote = analyze_quote(
            {
                "symbol": normalized,
                "name": normalized,
                "market": "CN",
                "last_price": 0,
                "change_pct": 0,
                "change_abs": 0,
                "prev_close": 0,
                "open": 0,
                "high": 0,
                "low": 0,
                "volume": 0,
                "turnover": 0,
                "bid": 0,
                "ask": 0,
                "spread_bps": 0,
                "volume_ratio": 1,
                "volatility_pct": 0,
                "provider": "quote_unavailable",
                "ts_event": None,
            },
            hermes_mode=hermes_mode,
        )
        if quote_error is None:
            quote_error = "未获取到实时行情"
    kline_error = None
    try:
        kline_rows = _load_daily_kline(normalized)
    except HTTPException as exc:
        kline_rows = []
        kline_error = str(exc.detail)
    except Exception as exc:
        kline_rows = []
        kline_error = f"K线获取失败: {exc}"
    kline_analysis = analyze_kline_rows(kline_rows)
    position = _load_positions_by_symbol().get(normalized)
    decision = analyze_position_logic(quote, kline_analysis, position)
    return {
        "quote": quote,
        "kline": kline_analysis,
        "kline_error": kline_error,
        "quote_error": quote_error,
        "position": position,
        "decision": decision,
    }


def _build_summary(hermes_mode: str = "normal") -> dict[str, Any]:
    watchlist = _live_watchlist_items()
    symbols = [item["symbol"] for item in watchlist]
    if not symbols:
        return {
            "market_pulse": market_pulse([]),
            "top_risks": [],
            "alerts": [],
            "quotes": [],
            "watchlist": watchlist,
            "as_of": utc_now_iso(),
            "data_freshness_sec": None,
        }

    quotes = _fetch_quotes(symbols)
    real_quotes = [quote for quote in quotes if quote.get("provider") == "tencent_quote"]
    analyses = [analyze_quote(quote, hermes_mode=hermes_mode) for quote in real_quotes]
    ranked = rank_analyses(analyses)
    pulse = market_pulse(ranked)

    as_of = utc_now_iso()
    if ranked and ranked[0].get("ts_event"):
        as_of = ranked[0]["ts_event"]
    freshness = None
    try:
        freshness = int((datetime.now(timezone.utc) - datetime.fromisoformat(as_of)).total_seconds())
    except ValueError:
        freshness = None

    return {
        "market_pulse": pulse,
        "top_risks": ranked,
        "alerts": [
            {
                "symbol": item["symbol"],
                "level": item["alert_level"],
                "risk_flags": item["risk_flags"],
                "summary": item["summary"],
            }
            for item in ranked
            if item.get("alert_level") in {"medium", "high"}
        ],
        "quotes": real_quotes,
        "watchlist": watchlist,
        "as_of": as_of,
        "data_freshness_sec": freshness,
    }


def _upsert_watchlist_item(symbol: str, note: str | None = None) -> dict[str, Any]:
    items = load_watchlist()
    now = utc_now_iso()
    for item in items:
        if item.get("symbol") == symbol:
            item["enabled"] = True
            if note is not None:
                item["note"] = note
            item["updated_at"] = now
            save_watchlist(items)
            return item

    created = {
        "symbol": symbol,
        "enabled": True,
        "note": note or "",
        "added_at": now,
        "updated_at": now,
    }
    items.append(created)
    save_watchlist(items)
    return created


def _disable_watchlist_item(symbol: str) -> dict[str, Any]:
    items = load_watchlist()
    now = utc_now_iso()
    for item in items:
        if item.get("symbol") == symbol:
            item["enabled"] = False
            item["updated_at"] = now
            save_watchlist(items)
            return item
    raise HTTPException(status_code=404, detail="watchlist symbol not found")


def _upsert_position(payload: PositionUpsertRequest) -> dict[str, Any]:
    symbol = _normalize_watch_symbol(payload.symbol)
    items = load_position_book()
    now = utc_now_iso()
    updates = payload.model_dump(exclude_unset=True)
    updates["symbol"] = symbol
    for item in items:
        if item.get("symbol") == symbol:
            item.update({key: value for key, value in updates.items() if value is not None or key in {"thesis", "horizon"}})
            item["updated_at"] = now
            save_position_book(items)
            return item

    created = {
        "symbol": symbol,
        "quantity": payload.quantity,
        "avg_cost": payload.avg_cost,
        "stop_loss": payload.stop_loss,
        "target_price": payload.target_price,
        "horizon": payload.horizon or "",
        "thesis": payload.thesis or "",
        "updated_at": now,
    }
    items.append(created)
    save_position_book(items)
    return created


def _run_monitor_cycle(hermes_mode: str = "normal") -> dict[str, Any]:
    config = load_monitor_config()
    status = load_monitor_status()
    cycle_started_at = utc_now_iso()

    try:
        summary = _build_summary(hermes_mode=hermes_mode)
        analyses = summary["top_risks"]
        pulse = summary["market_pulse"]
        previous_state = load_alert_state()
        events, new_state = detect_alert_events(
            analyses,
            previous_state,
            cooldown_minutes=int(config.get("cooldown_minutes", 15)),
            min_level=str(config.get("min_level", "medium")),
        )
        save_alert_state(new_state)

        outbox_records = build_outbox_records(events, target=config.get("target"), market_pulse_label=pulse.get("label"))
        if outbox_records:
            append_outbox(outbox_records)

        run_snapshot = {
            "recorded_at": utc_now_iso(),
            "hermes_mode": hermes_mode,
            "watchlist": summary["watchlist"],
            "market_pulse": pulse,
            "quotes": summary["quotes"],
            "top_risks": analyses,
            "alerts": events,
        }
        append_monitor_run(run_snapshot)
        append_analysis_snapshot(
            {
                "recorded_at": run_snapshot["recorded_at"],
                "market_pulse": pulse,
                "top_risks": analyses,
                "alert_count": len(events),
                "quote_count": len(summary["quotes"]),
            }
        )

        save_monitor_status(
            {
                **status,
                "last_run_at": cycle_started_at,
                "last_success_at": utc_now_iso(),
                "last_failure_at": status.get("last_failure_at"),
                "last_error": None,
                "last_alert_count": len(events),
                "last_quote_count": len(summary["quotes"]),
            }
        )
        return {
            "ok": True,
            "summary": summary,
            "alerts": events,
            "outbox_records": outbox_records,
            "delivery": {
                "mode": "outbox",
                "target": config.get("target"),
                "queued": len(outbox_records),
                "analysis_model": config.get("analysis_model"),
            },
            "monitor_status": load_monitor_status(),
        }
    except Exception as exc:
        save_monitor_status(
            {
                **status,
                "last_run_at": cycle_started_at,
                "last_failure_at": utc_now_iso(),
                "last_error": str(exc),
            }
        )
        raise


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")


@app.get("/styles.css")
def styles() -> FileResponse:
    return FileResponse(BASE_DIR / "styles.css")


@app.get("/app.js")
def app_js() -> FileResponse:
    return FileResponse(BASE_DIR / "app.js")


@app.get("/api/search")
def search_stocks(q: str = Query(..., min_length=1), limit: int = Query(default=20, ge=1, le=50)) -> dict[str, Any]:
    try:
        matches = _search_catalog(q, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"股票搜索失败: {exc}") from exc
    return {"query": q, "matches": matches}


@app.get("/api/quotes")
def quotes(symbols: str = Query(...)) -> dict[str, Any]:
    requested = [item.strip().upper() for item in symbols.split(",") if item.strip()]
    if not requested:
        raise HTTPException(status_code=400, detail="缺少股票代码")
    try:
        data = _fetch_quotes(requested)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"实时行情获取失败: {exc}") from exc
    return {"symbols": requested, "quotes": data}


@app.get("/api/watchlist")
def get_watchlist() -> dict[str, Any]:
    items = load_watchlist()
    return {"items": items, "enabled": [item for item in items if item.get("enabled", True)]}


@app.post("/api/watchlist")
def upsert_watchlist(payload: WatchlistUpsertRequest) -> dict[str, Any]:
    symbol = _normalize_watch_symbol(payload.symbol)
    item = _upsert_watchlist_item(symbol=symbol, note=payload.note)
    return {"item": item, "watchlist": load_watchlist()}


@app.delete("/api/watchlist/{symbol}")
def delete_watchlist(symbol: str) -> dict[str, Any]:
    normalized = _normalize_watch_symbol(symbol)
    item = _disable_watchlist_item(normalized)
    return {"item": item, "watchlist": load_watchlist()}


@app.get("/api/positions")
def get_positions() -> dict[str, Any]:
    return {"items": load_position_book()}


@app.post("/api/positions")
def upsert_position(payload: PositionUpsertRequest) -> dict[str, Any]:
    item = _upsert_position(payload)
    return {"item": item, "items": load_position_book()}


@app.get("/api/analysis/kline")
def analysis_kline(symbol: str = Query(...), limit: int = Query(default=120, ge=30, le=300)) -> dict[str, Any]:
    normalized = _normalize_watch_symbol(symbol)
    rows = _load_daily_kline(normalized, limit=limit)
    return {"symbol": normalized, "kline": analyze_kline_rows(rows)}


@app.get("/api/analysis/decision")
def analysis_decision(symbol: str = Query(...), hermes_mode: str = Query(default="normal")) -> dict[str, Any]:
    return _build_symbol_analysis(symbol, hermes_mode=hermes_mode)


@app.get("/api/risk-summary")
def risk_summary(hermes_mode: str = Query(default="normal")) -> dict[str, Any]:
    try:
        return _build_summary(hermes_mode=hermes_mode)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"风险摘要生成失败: {exc}") from exc


@app.post("/api/monitor/config")
def set_monitor_config(payload: MonitorConfigRequest) -> dict[str, Any]:
    current = load_monitor_config()
    updates = payload.model_dump(exclude_unset=True)
    if "min_level" in updates and updates["min_level"] not in {"low", "medium", "high"}:
        raise HTTPException(status_code=400, detail="min_level must be low, medium, or high")
    current.update(updates)
    save_monitor_config(current)
    return {"config": load_monitor_config()}


@app.get("/api/monitor/status")
def monitor_status() -> dict[str, Any]:
    watchlist = _enabled_watchlist_items()
    return {
        "runtime_dir": str(runtime_dir()),
        "watchlist_size": len(watchlist),
        "config": load_monitor_config(),
        "status": load_monitor_status(),
    }


@app.get("/api/monitor/history")
def monitor_history(limit: int = Query(default=20, ge=1, le=500)) -> dict[str, Any]:
    runs = load_monitor_runs()
    analyses = load_analysis_history()
    return {
        "monitor_runs": runs[-limit:],
        "analysis_history": analyses[-limit:],
    }


@app.post("/api/monitor/run-once")
def monitor_run_once(hermes_mode: str = Query(default="normal")) -> dict[str, Any]:
    try:
        return _run_monitor_cycle(hermes_mode=hermes_mode)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"监控循环执行失败: {exc}") from exc


@app.get("/api/hermes/stock-monitors")
def hermes_stock_monitors() -> dict[str, Any]:
    return {"items": load_monitor_jobs()}


@app.post("/api/hermes/stock-monitors")
def create_hermes_stock_monitor(payload: StockMonitorRequest) -> dict[str, Any]:
    try:
        job = register_stock_monitor(
            symbol=payload.symbol,
            interval_minutes=payload.interval_minutes,
            hermes_mode=payload.hermes_mode,
            note=payload.note,
            target=payload.target,
            thresholds=payload.thresholds,
        )
        run_result = None
        if payload.run_now:
            run_result = run_registered_monitors(symbols=[job["symbol"]], only_due=False, hermes_mode=payload.hermes_mode)
        return {"item": job, "run_result": run_result}
    except StockAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Hermes 股票监控创建失败: {exc}") from exc


@app.patch("/api/hermes/stock-monitors/{symbol}")
def patch_hermes_stock_monitor(symbol: str, payload: StockMonitorPatchRequest) -> dict[str, Any]:
    try:
        updates = payload.model_dump(exclude_unset=True)
        item = update_monitor_job(symbol, updates)
        return {"item": item}
    except StockAnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Hermes 股票监控更新失败: {exc}") from exc


@app.post("/api/hermes/stock-monitors/run")
def run_hermes_stock_monitors(
    symbols: str | None = Query(default=None),
    only_due: bool = Query(default=True),
    hermes_mode: str | None = Query(default=None),
    queue_alerts: bool = Query(default=True),
) -> dict[str, Any]:
    requested = [item.strip() for item in (symbols or "").split(",") if item.strip()]
    try:
        return run_registered_monitors(
            symbols=requested or None,
            only_due=only_due,
            hermes_mode=hermes_mode,
            queue_alerts=queue_alerts,
        )
    except StockAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Hermes 股票监控运行失败: {exc}") from exc


@app.get("/api/hermes/stock-monitors/realtime/status")
def hermes_realtime_monitor_status() -> dict[str, Any]:
    return {"status": get_realtime_monitor_status()}


@app.get("/api/hermes/stock-monitors/{symbol}/history")
def hermes_stock_history(symbol: str, limit: int = Query(default=240, ge=1, le=2000)) -> dict[str, Any]:
    try:
        normalized = _normalize_watch_symbol(symbol)
        history = load_stock_history(normalized, limit=limit)
        return {"symbol": normalized, "items": history, "count": len(history)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Hermes 股票历史读取失败: {exc}") from exc


@app.get("/api/hermes/stock-monitors/{symbol}/query")
def hermes_stock_query(
    symbol: str,
    lookback: int = Query(default=240, ge=1, le=2000),
    hermes_mode: str = Query(default="normal"),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        return build_stock_query(symbol, lookback=lookback, hermes_mode=hermes_mode, refresh=refresh)
    except StockAnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Hermes 股票查询失败: {exc}") from exc


@app.get("/api/hermes/stock-monitors/{symbol}/analysis")
def hermes_stock_analysis(
    symbol: str,
    lookback: int = Query(default=240, ge=1, le=2000),
    hermes_mode: str = Query(default="normal"),
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        return build_stock_analysis(symbol, lookback=lookback, hermes_mode=hermes_mode, refresh=refresh)
    except StockAnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Hermes 股票分析失败: {exc}") from exc


@app.get("/api/hermes/capabilities")
def hermes_capabilities() -> dict[str, Any]:
    return build_capability_answer_template()
