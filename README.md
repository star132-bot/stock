# Hermes Stock Sentinel

面向股农群体的单用户股票监控工作台。

当前实现版本：

- `v1.0.0` 已完成

当前版本目标：

- 搜索股票并自动加入关注池
- 查看股票实时状态
- 由 Hermes 持续监控风险
- 在股市异动和紧急崩坏时提醒用户
- 帮助用户保住收益并快速响应

## v1.0.0 已完成功能

### 股票搜索与关注

- 支持 A 股代码和名称搜索
- 支持裸代码输入，例如 `688766`
- 搜索命中后自动加入关注池
- 支持最近搜索记录
- 支持关注池增删和默认关注池重置

### 实时行情与看板

- 支持 A 股腾讯实时行情刷新
- 支持单股和关注池批量刷新
- 支持市场总览、实时价格、涨跌幅、成交量、量比、振幅、买卖价差
- 真实行情股票参与 Hermes 风险排行，静态样本不参与风险排行

### K 线与技术分析

- 支持日 K 线图展示
- 支持 MA5 / MA10 / MA20 / MA60
- 支持成交量均线
- 支持支撑位、压力位、趋势标签、量价总结
- K 线数据源优先使用 `akshare`，失败后自动回退到腾讯 K 线接口
- 历史 K 线会缓存到 `.runtime/kline_cache/`

### Hermes 风控

- 动量分
- 流动性分
- 波动稳定度
- 收益保护分
- 风险标签
- 风险等级
- 关注股风险优先级排行
- 风险检查清单
- Hermes 快讯事件流

### 持仓与投资判断

- 支持通过 `/api/positions` 写入持仓数量、成本价、止损位、目标位、持有周期和买入逻辑
- 支持 `/api/analysis/decision` 生成继续持有 / 观察 / 减仓 / 卖出判断
- K 线不可用时，行情和投资判断仍会返回，页面会显示明确错误，不再空白

### 告警与复盘

- 支持 `/api/monitor/run-once` 手动运行一次监控
- 支持告警去重和 cooldown
- 支持 outbox 待发送队列
- 支持 Server 酱、PushPlus、企业微信机器人
- 支持每晚 21:00 生成复盘总结文档

## 当前内容

- `index.html`: 页面入口
- `styles.css`: Hermes 工作台样式
- `app.js`: 前端交互、实时刷新、K 线渲染、Hermes 风控展示
- `server.py`: 搜索、行情、K 线、监控、风险摘要 API
- `sender.py`: 待发送告警 outbox sender
- `docs/DATA_PROVIDER_RESEARCH.md`: 实时数据源调研
- `docs/ANALYSIS_ENGINE_PLAN.md`: 专业化股票分析处理机制
- `docs/LIVE_INTEGRATION_BLUEPRINT.md`: 真实接入蓝图与标准化字段建议
- `docs/V1_0_0_PRODUCT_SPEC.md`: `v1.0.0` 功能定义
- `docs/V1_0_0_WORKFLOW.md`: `v1.0.0` 工作流
- `docs/V1_0_0_RELEASE.md`: `v1.0.0` 发布说明
- `docs/HERMES_PROJECT_OVERVIEW.md`: 项目全功能概要
- `docs/HERMES_OPERATOR_RUNBOOK.md`: Hermes 使用与运维手册

## 运行方式

初始化：

```bash
cd stock-realtime-dashboard
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

启动：

```bash
bash scripts/start_local_server.sh
```

然后打开：

- `http://127.0.0.1:8130`

如果机器上默认 `python3` 低于 3.10，可以指定 Python：

```bash
HERMES_PYTHON_BIN=/path/to/python3.11 bash scripts/start_local_server.sh
```

## 页面使用方式

1. 打开 `http://127.0.0.1:8130`
2. 在左侧搜索框输入股票代码或名称，例如 `688766`
3. 点击“搜索并自动关注”
4. 在关注池中点击股票切换当前标的
5. 查看实时行情、Hermes 风险分、K 线图、持仓逻辑和投资判断
6. 如需录入持仓，用 `/api/positions` 写入成本、止损和目标价
7. 如需生成告警，用 `/api/monitor/run-once` 手动运行一次监控

## 简化股票监控

如果不需要网页，可以使用本地简化版本：

- 程序入口：`simplified_stock_monitor.py`
- 双击启动：`disk/启动 简化股票监控.command`
- 本地原生窗口版：`native/SimplifiedStockMonitorApp.swift`
- 本地窗口双击启动：`disk/启动 简化股票监控图形版.command`

这两个版本都不启动 FastAPI，不打开浏览器，直接调用 Python 模块完成股票搜索、关注池、行情、K 线、Hermes 风控、持仓、告警和夜间总结。

如果想要“像网页一样但更简略”的本地窗口，双击：

```text
disk/启动 简化股票监控图形版.command
```

图形版提供：

- 股票搜索并加入关注
- 关注池列表
- 实时行情刷新
- Hermes 风控结果
- 投资判断
- 简化 K 线蜡烛图
- 运行一次监控
- 发送 outbox 告警

图形版是 macOS AppKit 原生窗口，不是浏览器页面，也不启动本地服务器。

如果想要纯终端菜单，双击：

```text
disk/启动 简化股票监控.command
```

终端版启动后会进入菜单：

```text
1. 搜索股票并加入关注
2. 查看关注池
3. 移出关注
4. 查看实时行情
5. 查看 Hermes 分析/K线/投资判断
6. 录入持仓逻辑
7. 配置 Hermes 告警
8. 运行一次 Hermes 监控
9. 发送 outbox 告警
10. 生成夜间总结
11. 查看运行状态
0. 退出
```

也可以直接用命令：

```bash
python3 simplified_stock_monitor.py search 688766
python3 simplified_stock_monitor.py add 688766.SH --note 芯片观察
python3 simplified_stock_monitor.py quotes 688766.SH
python3 simplified_stock_monitor.py analyze 688766.SH
python3 simplified_stock_monitor.py position 688766.SH --quantity 100 --avg-cost 255.4 --stop-loss 238 --target-price 290
python3 simplified_stock_monitor.py config-alerts --target pushplus:YOUR_TOKEN --cooldown-minutes 15 --min-level medium
python3 simplified_stock_monitor.py run-monitor
python3 simplified_stock_monitor.py send-alerts
python3 simplified_stock_monitor.py nightly-summary
```

## Hermes 连接方式

这里的 Hermes 由三部分组成：

- 前端 Hermes 控制台：页面里的风险展示、快讯和问答区
- 后端 Hermes 风控引擎：`server.py`、`alert_engine.py`、`technical_analysis.py`
- Hermes 告警发送器：`sender.py` 和 `scripts/send_pending_alerts.py`

### 1. 配置关注股票

```bash
curl -X POST http://127.0.0.1:8130/api/watchlist \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"688766.SH","note":"芯片观察"}'
```

### 2. 配置 Hermes 告警目标

支持三类目标：

- `serverchan:SCTxxxxxxxx`
- `pushplus:token`
- `wecom_bot:key`

示例：

```bash
curl -X POST http://127.0.0.1:8130/api/monitor/config \
  -H 'Content-Type: application/json' \
  -d '{"target":"pushplus:YOUR_TOKEN","cooldown_minutes":15,"min_level":"medium"}'
```

### 3. 运行一次 Hermes 监控

```bash
curl -X POST 'http://127.0.0.1:8130/api/monitor/run-once?hermes_mode=normal'
```

这一步会：

- 拉取关注池行情
- 计算风险分
- 生成风险事件
- 写入 `.runtime/outbox.json`
- 保存监控记录和分析快照

### 4. 发送 Hermes 告警

```bash
python3 scripts/send_pending_alerts.py
```

重试失败告警：

```bash
python3 scripts/send_pending_alerts.py --retry-failed
```

## 公网预览

已经加入 Cloudflare 临时公网分享脚本，适合在买服务器前先把原型发到公网查看。

启动公网分享：

```bash
cd stock-realtime-dashboard
bash scripts/start_public_share.sh
```

停止分享：

```bash
bash scripts/stop_public_share.sh
```

查询当前公网地址：

```bash
bash scripts/query_public_share.sh
```

详细说明见：

- `docs/PUBLIC_SHARE_SETUP.md`

## Hermes 告警发送

后端监控现在会把待发送消息写入：

- `.runtime/outbox.json`

支持的发送目标格式：

- `serverchan:SCTxxxxxxxx`
- `pushplus:token`
- `wecom_bot:key`

查看支持目标：

```bash
cd stock-realtime-dashboard
python3 scripts/send_pending_alerts.py --help-targets
```

手动发送待处理告警：

```bash
cd stock-realtime-dashboard
python3 scripts/send_pending_alerts.py
```

重试失败告警：

```bash
cd stock-realtime-dashboard
python3 scripts/send_pending_alerts.py --retry-failed
```

推荐流程：

1. `POST /api/watchlist` 添加监控股票
2. `POST /api/monitor/config` 配置目标通道
3. `POST /api/monitor/run-once` 生成风险事件并写入 outbox
4. 运行 `python3 scripts/send_pending_alerts.py`
5. 在微信或企业微信里确认收到消息

## 当前状态

`v1.0.0` 已完成并可本地运行。当前系统已经接入真实 A 股行情、K 线数据、Hermes 风控分析、告警 outbox 和夜间总结。

运行与使用文档：

- `docs/HERMES_PROJECT_OVERVIEW.md`
- `docs/HERMES_OPERATOR_RUNBOOK.md`
- `docs/V1_0_0_RELEASE.md`

后续版本可以继续接入：

- Polygon / Massive
- Alpaca Market Data
- Tushare

并扩展为多用户、后台常驻监控和更完整的策略回测。
