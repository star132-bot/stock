# Hermes Stock Sentinel v1.0.0 Release

发布日期：2026-04-29

## 状态

`v1.0.0` 开发完成。

这是 Hermes Stock Sentinel 的第一个可运行版本，定位为单用户股票监控工作台，已支持本地启动、A 股实时行情、K 线分析、Hermes 风险判断、告警 outbox 和夜间复盘。

## 核心能力

- 股票搜索：支持 A 股代码、名称、裸代码搜索。
- 关注池：搜索后自动加入关注池，支持移除、重置、最近搜索。
- 实时行情：通过腾讯行情接口刷新 A 股价格、涨跌幅、成交量、量比和振幅。
- K 线分析：支持日 K、MA5、MA10、MA20、MA60、成交量均线、支撑位、压力位和量价总结。
- K 线容错：优先使用 akshare，失败后回退腾讯 K 线接口，并缓存历史数据。
- Hermes 风控：输出动量分、流动性分、波动分、保护分、风险标签和风险等级。
- 投资判断：结合行情、K 线和持仓数据输出继续持有、观察、减仓、卖出判断。
- 告警中心：支持风险事件、去重、cooldown、outbox 队列。
- 消息发送：支持 Server 酱、PushPlus、企业微信机器人。
- 复盘沉淀：支持分析快照、监控记录和每晚总结文档。

## 运行方式

```bash
cd stock-realtime-dashboard
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/start_local_server.sh
```

访问：

```text
http://127.0.0.1:8130
```

如果默认 Python 版本低于 3.10：

```bash
HERMES_PYTHON_BIN=/path/to/python3.11 bash scripts/start_local_server.sh
```

## Hermes 使用流程

1. 搜索股票，例如 `688766`。
2. 系统自动加入关注池。
3. 页面展示实时行情、K 线、风险分和投资判断。
4. 配置告警目标：

```bash
curl -X POST http://127.0.0.1:8130/api/monitor/config \
  -H 'Content-Type: application/json' \
  -d '{"target":"pushplus:YOUR_TOKEN","cooldown_minutes":15,"min_level":"medium"}'
```

5. 手动运行一次监控：

```bash
curl -X POST 'http://127.0.0.1:8130/api/monitor/run-once?hermes_mode=normal'
```

6. 发送 outbox 告警：

```bash
python3 scripts/send_pending_alerts.py
```

## 主要 API

- `GET /api/search?q=688766`
- `GET /api/quotes?symbols=688766.SH`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `DELETE /api/watchlist/{symbol}`
- `GET /api/analysis/kline?symbol=688766.SH`
- `GET /api/analysis/decision?symbol=688766.SH`
- `GET /api/risk-summary`
- `POST /api/monitor/config`
- `GET /api/monitor/status`
- `POST /api/monitor/run-once`

## 验证记录

- `node --check app.js` 通过。
- Python `py_compile` 通过。
- 本地 `http://127.0.0.1:8130` 启动成功。
- `688766.SH` 行情接口返回正常。
- `688766.SH` K 线接口返回 60 根 bars，`kline_error` 为 `null`。

## 后续方向

- 常驻定时监控进程。
- 更完整的多账户/多用户配置。
- 更细的策略回测和风险规则评估。
- 接入 Tushare、Polygon、Alpaca 等更多数据源。
