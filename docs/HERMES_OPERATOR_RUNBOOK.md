# Hermes Operator Runbook

## 1. 克隆后初始化

```bash
cd stock-realtime-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果你机器上已经有可用 Python 环境，也可以直接安装：

```bash
pip install -r requirements.txt
```

## 2. 启动服务

```bash
bash scripts/start_local_server.sh
```

默认地址：

- `http://127.0.0.1:8130`

## 3. 配置关注股票

后端接口：

- `POST /api/watchlist`

示例：

```bash
curl -X POST http://127.0.0.1:8130/api/watchlist \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"688766.SH","note":"芯片观察"}'
```

## 4. 配置消息目标

后端接口：

- `POST /api/monitor/config`

示例：

```bash
curl -X POST http://127.0.0.1:8130/api/monitor/config \
  -H 'Content-Type: application/json' \
  -d '{"target":"pushplus:YOUR_TOKEN","cooldown_minutes":15,"min_level":"medium"}'
```

支持：

- `serverchan:SCTxxxxxx`
- `pushplus:token`
- `wecom_bot:key`

## 5. 手动跑一次监控

```bash
curl -X POST 'http://127.0.0.1:8130/api/monitor/run-once?hermes_mode=normal'
```

## 6. 发送待处理告警

```bash
python3 scripts/send_pending_alerts.py
```

查看支持目标：

```bash
python3 scripts/send_pending_alerts.py --help-targets
```

重试失败告警：

```bash
python3 scripts/send_pending_alerts.py --retry-failed
```

## 7. 持仓逻辑录入

示例：

```bash
curl -X POST http://127.0.0.1:8130/api/positions \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol":"688766.SH",
    "quantity":100,
    "avg_cost":255.4,
    "stop_loss":238,
    "target_price":290,
    "horizon":"波段",
    "thesis":"看好芯片景气与产品周期"
  }'
```

## 8. 查看 K线和投资判断

K线分析：

```bash
curl 'http://127.0.0.1:8130/api/analysis/kline?symbol=688766.SH'
```

投资判断：

```bash
curl 'http://127.0.0.1:8130/api/analysis/decision?symbol=688766.SH'
```

## 9. 每晚 9 点写总结

手动执行：

```bash
python3 scripts/generate_nightly_summary.py
```

输出目录：

- `docs/nightly_summaries/YYYY-MM-DD.md`

macOS crontab 示例：

```cron
0 21 * * * cd /Users/yourname/project/stock-realtime-dashboard && /usr/bin/python3 scripts/generate_nightly_summary.py
```

## 10. Hermes 如何使用

Hermes 的标准使用流程：

1. 搜索股票
2. 自动加入关注池
3. 跑监控
4. 查看 `/api/risk-summary`
5. 读取 `.runtime/outbox.json`
6. 发送待处理告警
7. 每晚生成总结文档

Hermes 应重点关注：

- 高风险股票
- 连续多次 high 的股票
- 市场态势从“可控状态”切换到“防守区间”或“紧急崩坏”的时点

## 11. 核心运行文件

- `server.py`: 后端 API 和监控循环
- `alert_engine.py`: 风险分析与告警规则
- `monitor_runtime.py`: runtime 文件读写
- `sender.py`: outbox sender
- `technical_analysis.py`: K线、量价、持仓判断
- `scripts/send_pending_alerts.py`: 手动发送脚本
- `scripts/generate_nightly_summary.py`: 夜间总结脚本

## 12. 需要保存和备份的内容

建议持续保留 `.runtime/` 和 `docs/nightly_summaries/`，因为这里包含：

- 监控数据
- 告警记录
- 投资复盘信息

这些数据是后续分析股票投资价值的基础。
