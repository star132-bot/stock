---
name: hermes-fast-stock-data
description: In-repo Hermes skill for fast stock data access and analysis in stock-realtime-dashboard. Use when Hermes needs to answer stock status, trend, buy/sell, monitoring, capability, or "why is it slow" questions by reading local snapshots/API first, avoiding unnecessary live refreshes, and only collecting new A-share data when required.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [stock-dashboard, a-share, fast-data, local-cache, analysis, hermes]
---

# Hermes Fast Stock Data

Use this skill when the user asks Hermes to:
- 查询某只股票现在怎么样。
- 分析未来趋势、是否买入、继续持有、减仓或卖出。
- 开启、查看或解释实时监控。
- 说明 Hermes 具备哪些股票监控和分析能力。
- 解释为什么 Hermes 获取数据慢，或怎样快速获取数据。

## Core Rule

Fast path first: read local snapshots and local analysis outputs before doing network collection.

Do not start from broad web search, fresh quote fetching, or `--force` unless the user explicitly asks to刷新, there is no local snapshot, or the local snapshot is too stale for the requested decision.

## Data Paths

Runtime data lives outside the skill folder and must not be committed:

```text
.runtime/hermes_stock_monitors.json
.runtime/hermes_realtime_monitor.json
.runtime/hermes_realtime_monitor.log
.runtime/stock_latest/<SYMBOL>.json
.runtime/stock_snapshots/<SYMBOL>.jsonl
.runtime/analysis_history.jsonl
.runtime/outbox.json
```

Meaning:
- `stock_latest/<SYMBOL>.json` is the fastest current snapshot.
- `stock_snapshots/<SYMBOL>.jsonl` is local history for trend and interval comparison.
- `hermes_stock_monitors.json` is the registered monitoring job list.
- `hermes_realtime_monitor.json` tells whether the background loop is running.
- `outbox.json` holds pending alerts.

## Preferred Query Order

From the repository root:

```bash
python3 scripts/hermes_stock_monitor.py query 688766.SH
```

This reads `.runtime/stock_latest` and `.runtime/stock_snapshots` first. It only collects if no snapshot exists, or if `--refresh` is passed.

For trend and buy/sell analysis:

```bash
python3 scripts/hermes_stock_monitor.py analyze 688766.SH --lookback 240
```

This is also local-history first. Do not pass `--refresh` by default.

If the API server is already running at `127.0.0.1:8130`, use:

```bash
curl -sS http://127.0.0.1:8130/api/hermes/stock-monitors/688766.SH/query
curl -sS http://127.0.0.1:8130/api/hermes/stock-monitors/688766.SH/analysis
```

Use `?refresh=true` only when a fresh network collection is required.

## Monitoring Workflow

When the user says “监控 688766.SH”:

```bash
python3 scripts/hermes_stock_monitor.py add 688766.SH --interval-minutes 30 --run-now
python3 scripts/hermes_stock_monitor.py start --poll-seconds 60
python3 scripts/hermes_stock_monitor.py status
```

When the user asks “现在有哪些股票在监控”:

```bash
python3 scripts/hermes_stock_monitor.py status
```

When the user asks to run one cycle:

```bash
python3 scripts/hermes_stock_monitor.py run
```

Use `--force` only for a user-requested immediate refresh or a manual diagnostic. Normal Hermes scheduled work should let `only_due=True` skip jobs that are not due.

## API Equivalents

```text
POST /api/hermes/stock-monitors
POST /api/hermes/stock-monitors/run
GET  /api/hermes/stock-monitors/realtime/status
GET  /api/hermes/stock-monitors/{symbol}/query
GET  /api/hermes/stock-monitors/{symbol}/history
GET  /api/hermes/stock-monitors/{symbol}/analysis
GET  /api/hermes/capabilities
```

Use the API when the local server is already running. Use the CLI when Hermes is operating directly in the repository or the server is unavailable.

## Slow Data Rules

Hermes may run slowly when live quote or K-line providers have DNS, timeout, anti-bot, or market-closed delays.

To stay fast:
- Prefer `query` and `analyze` without refresh.
- Prefer `run` without `--force`; let interval checks skip non-due symbols.
- Keep background monitor running so user-facing answers read already-collected data.
- If `quote_error` is present, surface it and lower confidence.
- If `provider` is `cached_quote_fallback`, explain that the latest valid local quote was reused because live quote fetching failed.

Never treat a failed live quote with `last_price=0` as a real crash. The project should reuse the previous valid quote and mark `quote_error`.

## Analysis Fields To Read

For a concise user answer, read:
- `summary.last_price`, `summary.change_pct`, `summary.volume_ratio`
- `summary.alert_level`, `summary.signal_bias`, `summary.protection_score`
- `summary.technical_score`, `summary.trend_label`
- `summary.support_price`, `summary.resistance_price`
- `summary.interval_change_pct`, `summary.alert_required`
- `history_summary`
- `indicators.rsi14`, `indicators.macd`, `indicators.bollinger`, `indicators.ma_alignment`
- `analysis.expected_direction`, `analysis.confidence`, `analysis.positives`, `analysis.risks`
- `recommendation.label`, `recommendation.score`, `recommendation.position_sizing`, `recommendation.review_conditions`
- `summary.quote_error` and `summary.kline_error`

## Answer Template

Use this structure for stock status and decisions:

```text
股票：<symbol> <name>
数据状态：<latest recorded_at/provider/quote_error if any>
当前摘要：现价 <price>，涨跌幅 <change_pct>% ，量比 <volume_ratio>，区间涨跌 <interval_change_pct>%
趋势判断：<expected_direction>，置信度 <confidence>；技术面 <trend_label>/<ma_alignment>/<MACD>
风险点：<top risks and alert triggers>
操作倾向：<recommendation label>，评分 <score>；仓位 <position_sizing>
关键价位：支撑 <support_price>，压力 <resistance_price>，止损/复核 <review_conditions>
边界：这基于本地行情、K线和历史快照，不保证未来走势，不是投资建议。
```

For capability questions, use:

```bash
python3 scripts/hermes_stock_monitor.py capabilities --text
```

or:

```bash
curl -sS http://127.0.0.1:8130/api/hermes/capabilities
```

## Decision Boundaries

- A-share symbols are preferred: `688766.SH`, `300750.SZ`, `600519.SH`.
- Bare 6-digit symbols may be normalized by project logic, but explicit suffixes are safer.
- Do not invent news, fundamentals, financial reports, or insider information.
- Web/news search may be used only as an explicitly labeled supplement; it must not replace local snapshot data.
- If local history has fewer than 3 snapshots or live quote failed, state lower confidence.
- Output is risk-control and research support, not investment advice.

## Verification

After editing this skill or related Hermes data behavior:

```bash
python -m pytest tests/test_fast_stock_data_skill.py tests/test_stock_analysis_service.py -q
```
