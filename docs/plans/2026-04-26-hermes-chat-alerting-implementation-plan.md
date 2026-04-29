# Hermes Chat Alerting Implementation Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Turn the current dashboard from a browser-only watchlist into an event-driven monitoring agent that detects stock risk changes, analyzes the situation, and pushes alert summaries to the user via chat tools.

Architecture: Keep the browser as a view layer only. Move real quote polling, risk scoring, alert deduplication, and chat delivery to the FastAPI backend. The backend will own watchlists, snapshots, alert state, and delivery targets, while the frontend reads backend summaries instead of generating final conclusions locally.

Tech Stack: FastAPI, Python requests, pytest, in-repo JSON runtime state, Hermes send_message integration for Feishu/Weixin delivery.

Known environment facts:
- Current backend file: `server.py`
- Current frontend logic file: `app.js`
- Current real market coverage: A-shares via Tencent quotes
- Current chat targets available in this Hermes environment: Feishu DM and Weixin DM
- Current frontend alerting is local-only (`app.js` builds alert cards in memory and never sends externally)

---

## Current gap summary

1. `app.js` currently computes `deriveSignal()`, `priorityRecords()`, `marketPulse()`, `buildNewsFeed()`, and `hermesReply()` entirely in the browser.
2. `ensureStream()` refreshes only while the page is open.
3. `state.alertHistory` is ephemeral and per-browser-session.
4. No backend watchlist storage exists.
5. No backend risk-analysis endpoint exists.
6. No scheduled monitor loop exists.
7. No chat delivery pipeline exists.

Result: the current app is a dashboard, not yet an autonomous monitoring agent.

---

## Phase 1 MVP outcome

After Phase 1, the system must support:
- User-defined watchlist persisted on the backend
- Backend quote refresh loop for followed A-shares
- Backend risk scoring and market-pulse summary
- Alert trigger on risk change / threshold breach
- Alert deduplication and cooldown
- Chat delivery to one configured target
- Frontend reads backend risk summary instead of inventing its own final answer

Non-goals for Phase 1:
- Full US market live data
- WebSocket market ingestion
- LLM-based free-form analysis
- Multi-user auth system
- Complex database setup

---

## Proposed file map

Modify:
- `server.py`
- `app.js`
- `index.html`
- `README.md`

Create:
- `alert_engine.py`
- `monitor_runtime.py`
- `tests/test_alert_engine.py`
- `tests/test_monitor_api.py`
- `.runtime/watchlist.json` (generated at runtime)
- `.runtime/alert_state.json` (generated at runtime)
- `docs/plans/2026-04-26-hermes-chat-alerting-implementation-plan.md` (this file)

Optional create in Phase 2:
- `market_gateway.py`
- `tests/test_market_gateway.py`

---

## Backend data contracts

### Watchlist item

```json
{
  "symbol": "688766.SH",
  "enabled": true,
  "note": "半导体观察",
  "added_at": "2026-04-26T13:46:12+08:00"
}
```

### Quote snapshot

```json
{
  "symbol": "688766.SH",
  "name": "普冉股份",
  "market": "CN",
  "last_price": 95.12,
  "change_pct": -2.36,
  "change_abs": -2.30,
  "open": 97.00,
  "high": 97.40,
  "low": 94.85,
  "prev_close": 97.42,
  "volume": 123456,
  "turnover": 987654321,
  "bid": 95.10,
  "ask": 95.13,
  "spread_bps": 3.15,
  "volume_ratio": 1.82,
  "ts_event": "2026-04-26T13:45:57+08:00",
  "provider": "tencent_quote"
}
```

### Risk analysis output

```json
{
  "symbol": "688766.SH",
  "analysis": {
    "momentum_score": 31,
    "liquidity_score": 58,
    "volatility_score": 44,
    "protection_score": 28,
    "signal_bias": "崩坏警戒",
    "alert_level": "high",
    "risk_flags": ["drawdown_expanding", "volume_expansion"],
    "summary": "跌幅扩大且量比升高，进入高优先级复核区。"
  }
}
```

### Outbound alert payload

```json
{
  "event_id": "688766.SH|high|drawdown_expanding|2026-04-26T13:46",
  "symbol": "688766.SH",
  "level": "high",
  "headline": "688766.SH 回撤扩张，进入崩坏警戒",
  "body": "跌幅 -2.36%，量比 1.82，点差 3.15 bps，Hermes 建议优先复核仓位与支撑位。",
  "market_pulse": "防守区间",
  "cooldown_key": "688766.SH|drawdown_expanding"
}
```

---

## API additions

Add these endpoints to `server.py`:

1. `GET /api/watchlist`
   - Return persisted watchlist.

2. `POST /api/watchlist`
   - Add or enable a symbol.
   - Request body: `{ "symbol": "688766.SH", "note": "半导体" }`

3. `DELETE /api/watchlist/{symbol}`
   - Disable or remove symbol.

4. `GET /api/risk-summary`
   - Return latest backend-computed summaries for all watched symbols.
   - Include `market_pulse`, `top_risks`, `alerts`, `as_of`, `data_freshness_sec`.

5. `POST /api/monitor/run-once`
   - Pull latest quotes, recompute analysis, trigger alerts once.
   - For manual verification and testing.

6. `GET /api/monitor/status`
   - Return runtime status, last success, last failure, target channel, watchlist size.

7. `POST /api/monitor/config`
   - Set alert target and thresholds.
   - Request example:
     `{ "target": "feishu:oc_241b262250c120d106db8e813daacaa7", "cooldown_minutes": 15, "min_level": "medium" }`

---

## Detection rules for MVP

Implement in `alert_engine.py`.

### Shared scores
- `momentum_score`
- `liquidity_score`
- `volatility_score`
- `protection_score`
- `signal_bias`
- `alert_level`

### Phase 1 alert rules
1. `drawdown_expanding`
   - Trigger if `change_pct <= -2.0`
   - Escalate to high if `change_pct <= -3.0`

2. `liquidity_deterioration`
   - Trigger if `spread_bps >= 4.0`

3. `volume_expansion`
   - Trigger if `volume_ratio >= 1.8`

4. `volatility_overheat`
   - Trigger if intraday range pct or derived volatility crosses threshold

5. `market_stress`
   - Trigger if half or more watched symbols are in high-risk state

### Alert emission policy
- Only emit when a rule is newly triggered OR level escalates
- Suppress repeats within cooldown window
- Emit recovery message optionally in Phase 2, not required for MVP

---

## Task breakdown

### Task 1: Create failing tests for analysis scoring

Objective: Lock the backend scoring behavior before implementation.

Files:
- Create: `tests/test_alert_engine.py`
- Create: `alert_engine.py`

Step 1: Write failing test for signal derivation

```python
from alert_engine import analyze_quote


def test_analyze_quote_flags_high_risk_drawdown():
    quote = {
        "symbol": "688766.SH",
        "last_price": 95.12,
        "change_pct": -2.36,
        "change_abs": -2.30,
        "prev_close": 97.42,
        "bid": 95.10,
        "ask": 95.13,
        "volume_ratio": 1.82,
        "high": 97.40,
        "low": 94.85,
    }

    result = analyze_quote(quote, hermes_mode="normal")

    assert result["signal_bias"] in {"防守优先", "崩坏警戒"}
    assert result["alert_level"] in {"medium", "high"}
    assert "drawdown_expanding" in result["risk_flags"]
```

Step 2: Run test to verify failure

Run:
`pytest tests/test_alert_engine.py::test_analyze_quote_flags_high_risk_drawdown -v`

Expected: FAIL because `alert_engine.py` or `analyze_quote` does not exist yet.

Step 3: Write minimal implementation in `alert_engine.py`

Implement:
- `analyze_quote(quote, hermes_mode="normal")`
- helper to compute spread bps if missing
- helper to derive volatility pct if missing

Step 4: Run test to verify pass

Run:
`pytest tests/test_alert_engine.py::test_analyze_quote_flags_high_risk_drawdown -v`

Step 5: Commit

`git add tests/test_alert_engine.py alert_engine.py && git commit -m "feat: add backend risk scoring engine"`

---

### Task 2: Create failing tests for event generation and cooldown

Objective: Ensure alerts are event-driven and deduplicated.

Files:
- Modify: `tests/test_alert_engine.py`
- Modify: `alert_engine.py`

Step 1: Write failing tests

```python
from alert_engine import detect_alert_events


def test_detect_alert_events_emits_only_on_new_trigger():
    analysis = {
        "symbol": "688766.SH",
        "signal_bias": "崩坏警戒",
        "alert_level": "high",
        "risk_flags": ["drawdown_expanding"],
        "change_pct": -3.2,
        "volume_ratio": 1.9,
        "spread_bps": 2.5,
    }
    previous_state = {}

    first_events, state_after_first = detect_alert_events([analysis], previous_state, cooldown_minutes=15)
    second_events, _ = detect_alert_events([analysis], state_after_first, cooldown_minutes=15)

    assert len(first_events) == 1
    assert second_events == []
```

Step 2: Run test to verify failure

Run:
`pytest tests/test_alert_engine.py::test_detect_alert_events_emits_only_on_new_trigger -v`

Step 3: Implement minimal event state logic

Implement:
- `detect_alert_events(analyses, previous_state, cooldown_minutes)`
- state keyed by `symbol|flag`
- event creation with headline/body

Step 4: Run target test and full file

Run:
- `pytest tests/test_alert_engine.py::test_detect_alert_events_emits_only_on_new_trigger -v`
- `pytest tests/test_alert_engine.py -v`

Step 5: Commit

`git add tests/test_alert_engine.py alert_engine.py && git commit -m "feat: add alert deduplication and cooldown"`

---

### Task 3: Add runtime persistence helpers

Objective: Persist watchlist, monitor config, and alert state under `.runtime/`.

Files:
- Create: `monitor_runtime.py`
- Modify: `server.py`
- Create: `.runtime/watchlist.json` (runtime-generated)
- Create: `.runtime/alert_state.json` (runtime-generated)

Step 1: Write failing tests for persistence helpers

Create tests in `tests/test_monitor_api.py` for:
- load empty watchlist
- save and reload watchlist
- save and reload config
- save and reload alert state

Step 2: Run tests to verify failure

`pytest tests/test_monitor_api.py -v`

Step 3: Implement minimal runtime helpers

Implement functions:
- `load_watchlist()`
- `save_watchlist(items)`
- `load_monitor_config()`
- `save_monitor_config(config)`
- `load_alert_state()`
- `save_alert_state(state)`

Step 4: Run tests

`pytest tests/test_monitor_api.py -v`

Step 5: Commit

`git add tests/test_monitor_api.py monitor_runtime.py server.py && git commit -m "feat: add monitor runtime persistence"`

---

### Task 4: Add backend watchlist APIs

Objective: Move the source of truth for followed symbols to the backend.

Files:
- Modify: `server.py`
- Modify: `tests/test_monitor_api.py`

Step 1: Write failing API tests

Test with FastAPI `TestClient`:
- `GET /api/watchlist`
- `POST /api/watchlist`
- `DELETE /api/watchlist/{symbol}`

Step 2: Run tests to verify failure

`pytest tests/test_monitor_api.py -k watchlist -v`

Step 3: Implement endpoints

Rules:
- Normalize symbols to uppercase
- Only accept `.SH` / `.SZ` in Phase 1 if symbol is persisted directly
- Add `enabled=true` by default

Step 4: Run tests

`pytest tests/test_monitor_api.py -k watchlist -v`

Step 5: Commit

`git add tests/test_monitor_api.py server.py && git commit -m "feat: add backend watchlist apis"`

---

### Task 5: Add backend risk-summary API

Objective: Expose backend-computed conclusions that the frontend can trust.

Files:
- Modify: `server.py`
- Modify: `tests/test_monitor_api.py`
- Modify: `alert_engine.py`

Step 1: Write failing API test

Test expectations:
- `/api/risk-summary` returns `market_pulse`, `top_risks`, `alerts`, `quotes`, `as_of`
- only real provider quotes participate

Step 2: Run test to verify failure

`pytest tests/test_monitor_api.py -k risk_summary -v`

Step 3: Implement endpoint

Implementation shape:
- load watchlist
- fetch quotes using existing `_fetch_quotes()`
- analyze each quote with `analyze_quote()`
- compute market pulse from analyses
- return sorted `top_risks`

Step 4: Run tests

`pytest tests/test_monitor_api.py -k risk_summary -v`

Step 5: Commit

`git add tests/test_monitor_api.py server.py alert_engine.py && git commit -m "feat: add backend risk summary api"`

---

### Task 6: Add monitor run-once endpoint with alert delivery abstraction

Objective: Allow one-shot poll -> analyze -> detect -> deliver -> persist cycle.

Files:
- Modify: `server.py`
- Modify: `alert_engine.py`
- Modify: `monitor_runtime.py`
- Modify: `tests/test_monitor_api.py`

Step 1: Write failing test

Test a pure function first if possible:
- given quotes and existing alert state, returns new alerts and updated state

Then test API:
- `POST /api/monitor/run-once` returns generated alerts count and delivery summary

Step 2: Run test to verify failure

`pytest tests/test_monitor_api.py -k run_once -v`

Step 3: Implement minimal monitor loop

Implementation should:
- load watchlist
- fetch quotes
- analyze
- detect events
- persist alert state
- return delivery payloads

For app code, keep delivery behind a single function like:
- `deliver_alerts(events, config)`

Phase 1 delivery adapter can be a placeholder that returns payloads if Hermes tool injection is not yet wired into the web server process.

Important engineering note:
- `send_message` is a Hermes tool, not a normal Python library callable from the running FastAPI process.
- Therefore Phase 1 should separate detection from delivery transport.
- Recommended deployment mode: backend writes outbound alert events to `.runtime/outbox.json`, and Hermes cron job reads/sends them.

Step 4: Run tests

`pytest tests/test_monitor_api.py -k run_once -v`

Step 5: Commit

`git add tests/test_monitor_api.py server.py alert_engine.py monitor_runtime.py && git commit -m "feat: add one-shot monitor cycle"`

---

### Task 7: Add Hermes delivery worker using cron

Objective: Actually push alerts to chat tools without requiring the browser to stay open.

Files:
- Modify: `README.md`
- Optional create: `scripts/send_pending_alerts.py`

Step 1: Write the outbox contract

Example outbox record:

```json
{
  "target": "feishu:oc_241b262250c120d106db8e813daacaa7",
  "message": "[HIGH] 688766.SH 回撤扩张\n跌幅 -2.36%，量比 1.82，点差 3.15 bps\nHermes: 优先复核仓位与支撑位。",
  "event_id": "688766.SH|drawdown_expanding|2026-04-26T13:46"
}
```

Step 2: Add a self-contained cron prompt

The cron job should:
- read `.runtime/outbox.json`
- send unsent messages to configured target
- mark sent events
- report failures clearly

Step 3: Verify manually

Manual verification flow:
- add symbol to watchlist
- call `POST /api/monitor/run-once`
- inspect outbox file
- run cron/manual Hermes sender
- verify message received in Feishu or Weixin

Step 4: Commit

`git add README.md scripts/send_pending_alerts.py && git commit -m "feat: document hermes chat delivery worker"`

---

### Task 8: Switch frontend from local conclusions to backend truth

Objective: Prevent UI/answer drift like "TSLA is most dangerous" when only A-shares are live.

Files:
- Modify: `app.js`
- Modify: `index.html`

Step 1: Write failing browser-facing behavior test if test harness exists; otherwise define manual verification steps.

Manual failure to reproduce now:
- watchlist contains simulated US names and real CN names
- ask "当前最危险的股票是谁？"
- UI may answer from mixed local state

Step 2: Implement frontend changes

Change behavior:
- add `fetchRiskSummary()` in `app.js`
- use backend `/api/risk-summary` for:
  - top risk card
  - priority table
  - alert center
  - Hermes reply to risk questions
- mark non-real-provider symbols as `模拟`
- exclude non-real quotes from backend-truth rankings

Step 3: Verify

Manual:
- open dashboard
- search/add 688766, 600519, 300750
- ask Hermes who is most dangerous
- confirm response matches `/api/risk-summary`

Step 4: Commit

`git add app.js index.html && git commit -m "feat: connect frontend hermes views to backend risk summary"`

---

### Task 9: Add operator setup docs

Objective: Make the system usable for actual daily monitoring.

Files:
- Modify: `README.md`

Step 1: Document setup

Must include:
- start local server
- configure watchlist
- configure target channel
- run monitor once
- enable recurring monitor schedule
- inspect status
- understand alert cooldown behavior

Step 2: Verify docs against live commands

Step 3: Commit

`git add README.md && git commit -m "docs: add hermes alerting operator guide"`

---

## Delivery architecture decision

This is the most important implementation constraint.

Because the FastAPI app cannot directly call Hermes tools like `send_message`, the clean design is:

1. FastAPI backend detects events and writes outbox records
2. Hermes agent runs on a schedule and sends unsent outbox messages
3. Hermes agent marks outbox items as sent

This gives:
- autonomous monitoring
- chat delivery without browser tab
- clean separation between market processing and operator messaging

---

## Recommended cron topology

1. Market monitor cron (every 1m or 2m)
   - Call backend `POST /api/monitor/run-once`
   - Or run a local script that executes the same cycle

2. Outbox sender cron (every 1m)
   - Read `.runtime/outbox.json`
   - Send via Hermes `send_message`
   - Mark sent

If keeping it simpler, combine both into one Hermes cron job that:
- hits monitor endpoint
- reads outbox
- sends new alerts

---

## Acceptance criteria

The feature is complete when all are true:

- A watched A-share can be added without opening the frontend source code
- `POST /api/monitor/run-once` fetches live quotes and returns analysis output
- High-risk events create deduplicated outbox records
- Hermes can send alert messages to at least one configured target
- Frontend "most dangerous stock" answer matches backend risk summary
- Repeated polls do not spam identical alerts inside cooldown window
- Runtime state survives process restart via `.runtime/*.json`

---

## Manual verification checklist

1. Start app
   - `bash scripts/start_local_server.sh`

2. Add watchlist items
   - `688766.SH`
   - `600519.SH`
   - `300750.SZ`

3. Configure target
   - Feishu or Weixin DM

4. Run one monitor cycle
   - `POST /api/monitor/run-once`

5. Check:
   - `/api/risk-summary`
   - `.runtime/alert_state.json`
   - `.runtime/outbox.json`
   - received chat message

6. Re-run monitor cycle immediately
   - verify no duplicate alert during cooldown

7. Open dashboard and ask:
   - “当前最危险的股票是谁？”
   - confirm answer matches backend output

---

## Plain-language product interpretation

What you want is not merely “实时查询”.
You want an autonomous stock sentinel:
- it watches when the user is busy
- it detects meaningful changes
- it interprets market state
- it pushes only actionable alerts

That is achievable in this repo, but only if the final authority moves from the browser into the backend + Hermes delivery loop.
