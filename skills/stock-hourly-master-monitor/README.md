# stock-hourly-master-monitor

这个目录是 `stock-realtime-dashboard` 项目内置的 Hermes skill，用来把看盘台变成“每小时自动监控 + 历史对比 + 巨大波动提醒 + 投资可行性分析”的股票监控代理。

## 快速开始

在项目根目录执行：

```bash
python scripts/hermes_stock_monitor.py add 688766.SH --interval-minutes 30 --run-now
python scripts/hermes_stock_monitor.py analyze 688766.SH --lookback 240
```

旧的 skill-local 兼容入口：

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --symbol 688766.SH
```

监控多只股票：

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --symbols 688766.SH,300750.SZ,600519.SH
```

只看帮助：

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --help
```

## 每小时自动监控

用 Hermes cron 创建定时任务：

```text
schedule: every 1h
script/command: cd /Users/starfeld/project/stock-realtime-dashboard && python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py --symbols 688766.SH --target origin
```

新的项目主入口可改为：

```text
script/command: cd /Users/starfeld/project/stock-realtime-dashboard && python scripts/hermes_stock_monitor.py run --symbols 688766.SH --force
```

cron 的 prompt 应要求：

1. 运行 `python scripts/hermes_stock_monitor.py analyze 688766.SH --lookback 240`。
2. 用 MiniMax-M2.7-highspeed 或当前可用模型生成中文分析。
3. 如果 run 输出的 `results[].comparison.alert_required=true`，给用户发送巨大波动提醒。
4. 如果没有巨大波动，只保存记录，不打扰用户。

## 数据保存位置

```text
.runtime/hourly_stock_snapshots/<SYMBOL>.jsonl   每只股票一份小时快照
.runtime/hourly_master_runs.jsonl                每次 master 监控汇总
.runtime/hourly_master_alerts.jsonl              master 告警记录
.runtime/monitor_runs.jsonl                      项目原生监控运行记录
.runtime/analysis_history.jsonl                  项目原生分析历史
.runtime/outbox.json                             待发送提醒
.runtime/hermes_stock_monitors.json              项目主入口登记的监控任务
.runtime/stock_snapshots/<SYMBOL>.jsonl          项目主入口保存的股票快照
.runtime/stock_latest/<SYMBOL>.json              项目主入口保存的最新快照
```

## 巨大波动默认阈值

```text
上一小时价格变化 >= 3%
日内涨跌幅 >= 5%
量比 >= 3.0
量比 <= 0.30 且大于 0
开盘跳空 >= 2%
```

覆盖阈值：

```bash
python skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py \
  --symbol 688766.SH \
  --threshold hourly_move_pct=2.0 \
  --threshold day_change_pct=4.0
```

## 注意

- 当前主要面向 A 股。
- 美股/前端样本数据不要当成真实实时数据。
- outbox 只是排队提醒，真正发送需要 Hermes cron 或 `scripts/send_pending_alerts.py` 之类的发送步骤。
- 这不是投资建议，只是风控和研究辅助。
