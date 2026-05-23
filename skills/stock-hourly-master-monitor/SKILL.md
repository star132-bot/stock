---
name: stock-hourly-master-monitor
description: In-repo Hermes skill for turning stock-realtime-dashboard into an hourly A-share monitoring agent. Adds requested stocks to the watchlist, runs one-hour monitoring cycles, persists per-symbol JSONL history, compares current vs historical snapshots, builds expert investment feasibility prompts, and queues outbox alerts on huge volatility.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [stock-dashboard, a-share, hourly-monitoring, risk-alerts, minimax, clone-friendly]
---

# Stock Hourly Master Monitor

Use this skill when the user says any of the following:
- “帮我监控 688766.SH”
- “把茅台加入监控，每小时看一次”
- “我忙的时候你帮我盯着这只股票，有大波动提醒我”
- “分析当前和历史监控数据，看这只股票值不值得投”
- “给 stock-realtime-dashboard 配一个自动股票监控 agent”

This skill lives inside the cloned `stock-realtime-dashboard` repository. It is designed so another user can clone the project and immediately see the exact Hermes workflow, script, paths, thresholds, and cron template.

## Architecture

The skill does not create a second stock system. It reuses the existing project runtime:

1. User names one or more A-share symbols.
2. The preferred project runner is `scripts/hermes_stock_monitor.py`; the skill-local `scripts/hourly_master_monitor.py` remains as a clone-friendly Hermes example.
3. The script calls existing project logic:
   - `server._run_monitor_cycle()`
   - `server._build_symbol_analysis()`
   - `monitor_runtime.append_monitor_run()`
   - `monitor_runtime.append_analysis_snapshot()`
   - `monitor_runtime.append_outbox()`
4. Every run writes project-native monitor history and extra per-symbol hourly history.
5. The next hourly run compares the latest quote with the prior per-symbol snapshot.
6. Huge volatility writes a pending alert record to `.runtime/outbox.json` and returns a master-analysis prompt that Hermes/MiniMax can summarize and send.

## Files in this skill

```text
skills/stock-hourly-master-monitor/SKILL.md
skills/stock-hourly-master-monitor/README.md
skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py
skills/stock-hourly-master-monitor/examples/hermes-cron.yaml
```

Runtime data is intentionally outside the skill folder:

```text
.runtime/monitor_runs.jsonl
.runtime/analysis_history.jsonl
.runtime/hourly_master_runs.jsonl
.runtime/hourly_master_alerts.jsonl
.runtime/hourly_stock_snapshots/<SYMBOL>.jsonl
.runtime/outbox.json
```

Do not commit `.runtime/` data unless the project explicitly wants sample fixtures.

## Default thresholds for “huge volatility”

The script queues an alert if any condition is triggered:

```text
hourly_move_pct   >= 3.0% absolute move vs previous hourly snapshot
day_change_pct    >= 5.0% absolute intraday move
volume_ratio_high >= 3.0
volume_ratio_low  <= 0.30 and > 0
price_gap_pct     >= 2.0% absolute opening gap vs previous close
```

Override thresholds with repeated `--threshold key=value` arguments.

Example:

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py \
  --symbol 688766.SH \
  --threshold hourly_move_pct=2.0 \
  --threshold day_change_pct=4.0
```

## One-shot usage

Preferred project-native entry from the repository root:

```bash
cd /Users/starfeld/project/stock-realtime-dashboard
python scripts/hermes_stock_monitor.py add 688766.SH --interval-minutes 30 --run-now
python scripts/hermes_stock_monitor.py run
python scripts/hermes_stock_monitor.py analyze 688766.SH --lookback 240
```

Skill-local compatibility entry:

```bash
cd /Users/starfeld/project/stock-realtime-dashboard
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --symbol 688766.SH
```

Multiple stocks:

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py \
  --symbol 688766.SH \
  --symbol 300750.SZ \
  --symbol 600519.SH
```

Or comma-separated:

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --symbols 688766.SH,300750.SZ,600519.SH
```

If no symbol is passed, the script monitors every enabled A-share in `.runtime/watchlist.json`:

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py
```

## Hermes cron usage

Create a Hermes cron job that runs every hour. The prompt must be self-contained because cron runs in a fresh session.

Recommended cron prompt:

```text
你是 stock-realtime-dashboard 的股票监控代理。
项目路径：/Users/starfeld/project/stock-realtime-dashboard
任务：每小时运行一次项目内 skill 脚本，监控用户指定股票，保存历史，对比当前与上一小时快照，并在巨大波动时通过 outbox/聊天工具提醒用户。
执行：cd /Users/starfeld/project/stock-realtime-dashboard && python scripts/hermes_stock_monitor.py run --symbols 688766.SH --force
随后执行：cd /Users/starfeld/project/stock-realtime-dashboard && python scripts/hermes_stock_monitor.py analyze 688766.SH --lookback 240
读取 analyze 输出中的 recommendation、analysis、history_summary 和 indicators，用 MiniMax-M2.7-highspeed 或当前可用模型生成 300 字以内的中文投资可行性分析。
如果 run 输出的 results[].comparison.alert_required=true，必须发送提醒；如果 false，只记录运行结果，不要打扰用户。
分析要求：像专业股票大师一样，但风险优先，明确仓位、止损和是否值得投资；不要编造新闻或财报。
```

Schedule:

```text
every 1h
```

Use MiniMax for routine monitoring if available; GPT/Claude can be used for implementation and debugging.

## Exact agent procedure

When the user asks to monitor a stock:

1. Normalize the symbol.
   - `688766` -> `688766.SH` if inferred by project logic.
   - `300750` -> `300750.SZ` if inferred by project logic.
   - Explicit suffixes like `600519.SH` are preferred.
2. Run a one-shot check with the in-repo script.
3. Confirm the script wrote:
   - `.runtime/hourly_stock_snapshots/<SYMBOL>.jsonl`
   - `.runtime/hourly_master_runs.jsonl`
   - project monitor history files.
4. Create or update a Hermes cron job with `schedule="every 1h"`.
5. In the cron prompt, include the project path, symbol list, and alert policy.
6. If the user wants chat alerts, configure `--target` and/or have the cron final response delivered to the origin chat.
7. Never claim “continuous monitoring is enabled” until the cron job exists and has run successfully at least once.

## Expert-analysis checklist

Each hourly analysis should include:

```text
1. 当前价格与涨跌幅
2. 和上一小时快照的差异
3. 量比/成交量是否异常
4. 趋势状态：趋势确认 / 偏强跟踪 / 防守优先 / 崩坏警戒
5. 风险项：回撤、波动、流动性、跳空、放量
6. 投资可行性：可观察 / 可小仓试错 / 暂不适合 / 需减仓止损
7. 仓位建议
8. 止损位或复核条件
9. 数据不足或行情异常说明
10. “这不是投资建议，只是基于当前数据的风控分析”
```

## Verification commands

From repo root:

```bash
python -m pytest tests/test_hourly_master_monitor_skill.py -q
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --help
```

Optional live run, only when the user permits network/data-source access:

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --symbol 688766.SH --no-queue-alert
```

## Important boundaries

- Phase 1 supports A-shares only.
- A-share quote data comes through the project’s existing Tencent/AkShare-backed implementation.
- US stock/sample front-end records must not be treated as authoritative real-time data.
- The script writes alert records to outbox; another Hermes/send-message step is responsible for delivery.
- The analysis is risk-control support, not investment advice.
