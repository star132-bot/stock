# Hermes Stock Sentinel

面向股农群体的单用户股票监控工作台。

当前实现版本：

- `v1.0.0`

当前版本目标：

- 搜索股票并自动加入关注池
- 查看股票实时状态
- 由 Hermes 持续监控风险
- 在股市异动和紧急崩坏时提醒用户
- 帮助用户保住收益并快速响应

## 当前内容

- `index.html`: 页面入口
- `styles.css`: Hermes 工作台样式
- `app.js`: 前端交互、模拟实时推送、Hermes 风控逻辑
- `server.py`: 搜索、行情、监控、风险摘要 API
- `sender.py`: 待发送告警 outbox sender
- `docs/DATA_PROVIDER_RESEARCH.md`: 实时数据源调研
- `docs/ANALYSIS_ENGINE_PLAN.md`: 专业化股票分析处理机制
- `docs/LIVE_INTEGRATION_BLUEPRINT.md`: 真实接入蓝图与标准化字段建议
- `docs/V1_0_0_PRODUCT_SPEC.md`: `v1.0.0` 功能定义
- `docs/V1_0_0_WORKFLOW.md`: `v1.0.0` 工作流
- `docs/HERMES_PROJECT_OVERVIEW.md`: 项目全功能概要
- `docs/HERMES_OPERATOR_RUNBOOK.md`: Hermes 使用与运维手册

## 运行方式

初始化：

```bash
cd stock-realtime-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

启动：

```bash
bash scripts/start_local_server.sh
```

然后打开：

- `http://127.0.0.1:8130`

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

这是一个前端原型，不直接请求真实行情接口。

当前原型已经包含：

- 搜索股票
- 支持裸代码搜索（如 `688766`）
- 搜索命中后自动加入关注池
- 最近搜索记录
- 关注池管理
- A 股实时行情接口刷新
- 真实行情股票参与 Hermes 风险排行，静态样本不参与
- 市场总览卡片
- Hermes 多维保护评分
- 风险检查与快讯提醒
- 关注股风险优先级排行
- Hermes 告警中心
- K线与量价分析面板
- 持仓逻辑面板
- 投资判断面板
- `/api/analysis/kline`
- `/api/analysis/decision`
- `/api/positions`
- Hermes 对话控制台
- `/api/risk-summary` 后端风险摘要
- `/api/monitor/run-once` 一次性监控循环
- outbox 告警发送
- 每晚 9 点总结脚本

运行与使用文档：

- `docs/HERMES_PROJECT_OVERVIEW.md`
- `docs/HERMES_OPERATOR_RUNBOOK.md`

下一步可以按文档里的方案接入：

- Polygon / Massive
- Alpaca Market Data
- Tushare

并将模拟数据替换为真实数据流。
